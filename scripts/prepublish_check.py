#!/usr/bin/env python3
"""Block publication on privacy, attachment, resource, or link failures."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "docs" / "notes"
MAX_LOCAL_ATTACHMENT_SIZE = 20 * 1024 * 1024
ALLOWED_ATTACHMENT_SUFFIXES = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".csv",
    ".ipynb",
    ".json",
    ".txt",
}
RESTRICTED_TO_FILES_SUFFIXES = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
}
EXECUTABLE_SUFFIXES = {
    ".exe",
    ".msi",
    ".dll",
    ".so",
    ".dylib",
    ".scr",
    ".com",
    ".bat",
    ".cmd",
}
SECRET_SUFFIXES = {".env", ".key", ".pem", ".p12", ".pfx"}
HIGH_RISK_SEGMENTS = {
    "private",
    "internal",
    "secrets",
    "credentials",
    "raw-submission",
    "research-drafts",
}
IGNORED_SEGMENTS = {".git", "site", ".venv", "__pycache__", ".cache"}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".rst",
    ".csv",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".py",
    ".java",
    ".js",
    ".ts",
    ".rs",
    ".go",
    ".sh",
    ".ps1",
    ".html",
    ".css",
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


def add_error(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def is_ignored(path: Path) -> bool:
    return bool(IGNORED_SEGMENTS.intersection(path.parts))


def is_local_attachment(path: Path) -> bool:
    try:
        relative = path.relative_to(NOTES)
    except ValueError:
        return False
    return "files" in (part.lower() for part in relative.parts[:-1])


def validate_notes(errors: list[str]) -> None:
    if not NOTES.exists():
        errors.append("docs/notes: 笔记目录不存在")
        return
    for folder in sorted(item for item in NOTES.iterdir() if item.is_dir()):
        if not any(folder.rglob("*.md")):
            add_error(errors, folder, "笔记文件夹中没有 Markdown 文件")


def validate_resources(errors: list[str]) -> None:
    manifest_path = ROOT / "data" / "resources.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    required = {
        "course",
        "chapter",
        "title",
        "asset_url",
        "file_type",
        "size",
        "source",
        "rights_basis",
        "checksum",
        "approved",
    }
    for index, item in enumerate(manifest.get("resources", []), start=1):
        missing = required - set(item)
        if missing:
            errors.append(f"data/resources.yml item {index}: 缺少字段 {sorted(missing)}")
            continue
        if item["approved"]:
            parsed = urlparse(str(item["asset_url"]))
            if parsed.scheme != "https" or parsed.netloc != "github.com":
                errors.append(
                    f"data/resources.yml item {index}: "
                    "Release 附件必须使用 github.com HTTPS 地址"
                )
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(item["checksum"])):
                errors.append(
                    f"data/resources.yml item {index}: 校验值必须是 sha256: 加 64 位小写十六进制"
                )
            if not str(item["rights_basis"]).strip():
                errors.append(
                    f"data/resources.yml item {index}: 缺少公开授权依据"
                )


def validate_attachments_and_paths(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or is_ignored(path):
            continue

        lowered_parts = {part.lower() for part in path.relative_to(ROOT).parts}
        suffix = path.suffix.lower()
        if HIGH_RISK_SEGMENTS.intersection(lowered_parts):
            add_error(errors, path, "路径包含禁止公开的高风险目录名")
        if suffix in SECRET_SUFFIXES:
            add_error(errors, path, f"禁止公开密钥或环境文件 {suffix}")
        if suffix in EXECUTABLE_SUFFIXES:
            add_error(errors, path, f"禁止公开可执行文件 {suffix}")

        local_attachment = is_local_attachment(path)
        if suffix in RESTRICTED_TO_FILES_SUFFIXES and not local_attachment:
            add_error(
                errors,
                path,
                "下载附件必须放在 docs/notes/课程/章节/files/ 中",
            )
        if local_attachment:
            if suffix not in ALLOWED_ATTACHMENT_SUFFIXES:
                add_error(
                    errors,
                    path,
                    f"files/ 不允许此文件类型 {suffix or '(无扩展名)'}",
                )
            if path.stat().st_size > MAX_LOCAL_ATTACHMENT_SIZE:
                size_mib = path.stat().st_size / 1024 / 1024
                add_error(
                    errors,
                    path,
                    f"附件为 {size_mib:.1f} MiB，超过 20 MiB；请改用 learning-resources Release",
                )


def validate_privacy(errors: list[str]) -> None:
    candidates = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not is_ignored(path)
        and "vendor" not in path.parts
        and path.suffix.lower() in TEXT_SUFFIXES
    ]
    candidates += [
        path
        for path in (ROOT / "README.md", ROOT / "NOTICE.md")
        if path.exists() and path not in candidates
    ]
    for path in sorted(set(candidates)):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            add_error(errors, path, "公开文本不是 UTF-8 编码")
            continue
        text_for_patterns = text.replace("git@ssh.github.com", "")
        text_for_patterns = text_for_patterns.replace("git@github.com", "")
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text_for_patterns):
                add_error(errors, path, f"检测到{label}")
        for index in range(max(0, len(text) - 2)):
            digest = hashlib.sha256(text[index : index + 3].encode()).hexdigest()
            if digest in KNOWN_PRIVATE_NAME_DIGESTS:
                add_error(errors, path, "检测到受保护的真实姓名")
                break
        if re.search(
            r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}",
            text,
        ):
            add_error(errors, path, "检测到高置信度凭据格式")


def validate_links(errors: list[str]) -> None:
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for path in sorted((ROOT / "docs").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        prose = re.sub(r"(?ms)^(```|~~~).*?^\1[ \t]*$", "", text)
        prose = re.sub(r"`[^`\n]+`", "", prose)
        for raw in pattern.findall(prose):
            target = raw.split("#", 1)[0].strip().strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            target = unquote(target)
            if not (path.parent / target).resolve().exists():
                add_error(errors, path, f"内部链接不存在：{raw}")


def main() -> int:
    errors: list[str] = []
    validate_attachments_and_paths(errors)
    validate_privacy(errors)
    validate_resources(errors)
    validate_notes(errors)
    validate_links(errors)
    if errors:
        print("Publication gate failed:", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1
    print(
        "Publication gate passed: privacy, attachments, resources, note folders, and links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
