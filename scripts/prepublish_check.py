#!/usr/bin/env python3
"""Block publication on privacy, resource, or broken-link failures."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
DISALLOWED_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".zip", ".7z", ".rar", ".tar", ".gz", ".env", ".key", ".pem",
}
HIGH_RISK_SEGMENTS = {
    "private", "internal", "secrets", "credentials", "raw-submission",
    "research-drafts",
}
KNOWN_PRIVATE_NAME_DIGESTS = {
    "caca68d84fb9259e6761d39b092c6f2df305f4aaab190c70a9fe84db95da13a6"
}
SENSITIVE_PATTERNS = {
    "可能的学号": re.compile(r"(?<!\d)20\d{10}(?!\d)"),
    "中国大陆手机号": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "电子邮箱": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "私有 IPv4 地址": re.compile(
        r"\b(?:10\.\d{1,3}(?:\.\d{1,3}){2}|192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
    ),
    "疑似密钥": re.compile(
        r"(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}",
        re.I,
    ),
    "私钥头": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def add_error(errors, path, message):
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def validate_notes(errors):
    notes = ROOT / "docs" / "notes"
    if not notes.exists():
        errors.append("docs/notes: 笔记目录不存在")
        return
    for folder in sorted(item for item in notes.iterdir() if item.is_dir()):
        if not any(folder.rglob("*.md")):
            add_error(errors, folder, "笔记文件夹中没有 Markdown 文件")


def validate_resources(errors):
    manifest = yaml.safe_load((ROOT / "data/resources.yml").read_text(encoding="utf-8")) or {}
    required = {
        "course", "chapter", "title", "asset_url", "file_type", "size",
        "source", "rights_basis", "checksum", "approved",
    }
    for index, item in enumerate(manifest.get("resources", []), start=1):
        missing = required - set(item)
        if missing:
            errors.append(f"data/resources.yml item {index}: 缺少字段 {sorted(missing)}")
            continue
        if item["approved"]:
            parsed = urlparse(str(item["asset_url"]))
            if parsed.scheme != "https" or parsed.netloc != "github.com":
                errors.append(f"data/resources.yml item {index}: 附件必须使用 GitHub HTTPS 地址")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(item["checksum"])):
                errors.append(f"data/resources.yml item {index}: 校验值格式无效")
            if not str(item["rights_basis"]).strip():
                errors.append(f"data/resources.yml item {index}: 缺少公开授权依据")


def validate_privacy(errors):
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "site", ".venv"} for part in path.parts):
            continue
        if path.suffix.lower() in DISALLOWED_SUFFIXES:
            add_error(errors, path, f"站点仓库禁止附件类型 {path.suffix}")
        if HIGH_RISK_SEGMENTS.intersection(part.lower() for part in path.parts):
            add_error(errors, path, "路径包含高风险目录名")

    candidates = list((ROOT / "docs").rglob("*")) + list((ROOT / "data").rglob("*"))
    candidates += [ROOT / "README.md", ROOT / "NOTICE.md"]
    for path in sorted(item for item in candidates if item.is_file() and "vendor" not in item.parts):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            add_error(errors, path, "公开内容不是 UTF-8 文本")
            continue
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                add_error(errors, path, f"检测到{label}")
        for index in range(max(0, len(text) - 2)):
            digest = hashlib.sha256(text[index:index + 3].encode()).hexdigest()
            if digest in KNOWN_PRIVATE_NAME_DIGESTS:
                add_error(errors, path, "检测到受保护的真实姓名")
                break
        if re.search(r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}", text):
            add_error(errors, path, "检测到高置信度凭据格式")


def validate_links(errors):
    pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for path in sorted((ROOT / "docs").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for raw in pattern.findall(text):
            target = raw.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (path.parent / target).resolve().exists():
                add_error(errors, path, f"内部链接不存在：{raw}")


def main() -> int:
    errors = []
    validate_privacy(errors)
    validate_resources(errors)
    validate_notes(errors)
    validate_links(errors)
    if errors:
        print("Publication gate failed:", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("Publication gate passed: privacy, resources, note folders, and links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
