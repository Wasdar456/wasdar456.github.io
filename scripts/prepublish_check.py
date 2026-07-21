#!/usr/bin/env python3
"""Block publication when privacy, rights, metadata, or quality gates fail."""

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
HIGH_RISK_SEGMENTS = {"private", "internal", "secrets", "credentials", "raw-submission", "research-drafts"}
KNOWN_PRIVATE_NAME_DIGESTS = {
    "caca68d84fb9259e6761d39b092c6f2df305f4aaab190c70a9fe84db95da13a6"
}
SENSITIVE_PATTERNS = {
    "可能的学号": re.compile(r"(?<!\d)20\d{10}(?!\d)"),
    "中国大陆手机号": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "电子邮箱": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "私有 IPv4 地址": re.compile(r"\b(?:10\.\d{1,3}(?:\.\d{1,3}){2}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"),
    "疑似密钥": re.compile(r"(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}", re.I),
    "私钥头": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
COURSE_REQUIRED = ["学习目标", "前置知识", "核心概念", "推导", "例", "常见错误", "自测", "参考", "校对信息"]
PAPER_REQUIRED = ["论文地图", "问题", "方法", "公式", "训练", "实验", "证据", "局限", "复现", "关系", "阅读后仍未解决的问题", "审读结论"]


def add_error(errors, path, message):
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def parse_frontmatter(path, errors):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        add_error(errors, path, "缺少 YAML 元数据")
        return {}, text
    try:
        _, raw, body = text.split("---\n", 2)
        return yaml.safe_load(raw) or {}, body
    except (ValueError, yaml.YAMLError) as exc:
        add_error(errors, path, f"YAML 元数据无效：{exc}")
        return {}, text


def validate_quality(errors):
    courses = yaml.safe_load((ROOT / "data/courses.yml").read_text(encoding="utf-8"))["courses"]
    papers = yaml.safe_load((ROOT / "data/papers.yml").read_text(encoding="utf-8"))["papers"]
    note_paths = [ROOT / "docs" / note["path"] for course in courses for note in course["published_notes"]]
    paper_paths = [ROOT / "docs" / item["path"] for item in papers]

    for path in note_paths:
        if not path.exists():
            add_error(errors, path, "清单中的正式笔记不存在")
            continue
        metadata, body = parse_frontmatter(path, errors)
        missing = {"title", "course", "chapter", "status", "updated", "source_kind", "sources"} - set(metadata)
        if missing:
            add_error(errors, path, "缺少元数据：" + ", ".join(sorted(missing)))
        for heading in COURSE_REQUIRED:
            if heading not in body:
                add_error(errors, path, f"缺少质量章节：{heading}")
        if len(re.sub(r"\s", "", body)) < 1800:
            add_error(errors, path, "正式课程笔记正文少于 1800 个非空白字符")

    for path in paper_paths:
        if not path.exists():
            add_error(errors, path, "清单中的论文精读不存在")
            continue
        metadata, body = parse_frontmatter(path, errors)
        missing = {"title", "authors", "venue", "year", "topic", "paper_url", "code_url", "review_status", "last_reviewed"} - set(metadata)
        if missing:
            add_error(errors, path, "缺少论文元数据：" + ", ".join(sorted(missing)))
        for heading in PAPER_REQUIRED:
            if heading not in body:
                add_error(errors, path, f"缺少精读章节：{heading}")
        if len(re.sub(r"\s", "", body)) < 4500:
            add_error(errors, path, "论文精读正文少于 4500 个非空白字符")
        for tag in ["论文原文", "客观事实", "我们的解释", "尚未验证"]:
            if tag not in body:
                add_error(errors, path, f"缺少证据标签：{tag}")


def validate_resources(errors):
    manifest = yaml.safe_load((ROOT / "data/resources.yml").read_text(encoding="utf-8"))
    required = {"course", "chapter", "title", "asset_url", "file_type", "size", "source", "rights_basis", "checksum", "approved"}
    for index, item in enumerate(manifest.get("resources", []), start=1):
        missing = required - set(item)
        if missing:
            errors.append(f"data/resources.yml item {index}: 缺少字段 {sorted(missing)}")
            continue
        if item["approved"]:
            parsed = urlparse(str(item["asset_url"]))
            if parsed.scheme != "https" or "github.com" not in parsed.netloc:
                errors.append(f"data/resources.yml item {index}: 公开附件必须使用 GitHub HTTPS 地址")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(item["checksum"])):
                errors.append(f"data/resources.yml item {index}: 校验值格式无效")
            if not str(item["rights_basis"]).strip():
                errors.append(f"data/resources.yml item {index}: 缺少再分发授权依据")


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
    # Third-party modules are pinned and licensed separately. Scan authored
    # public content here; dependency code is covered by version and license
    # checks rather than by heuristics that produce false positives on bundles.
    for path in sorted({
        item for item in candidates
        if item.is_file() and "vendor" not in item.parts
    }):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            add_error(errors, path, "公开内容不是 UTF-8 文本")
            continue
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                add_error(errors, path, f"检测到{label}")
        for index in range(max(0, len(text) - 2)):
            if hashlib.sha256(text[index:index + 3].encode()).hexdigest() in KNOWN_PRIVATE_NAME_DIGESTS:
                add_error(errors, path, "检测到受保护的真实姓名")
                break
        if re.search(r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}", text):
            add_error(errors, path, "检测到高置信度凭据格式")


def validate_links(errors):
    pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for path in sorted((ROOT / "docs").rglob("*.md")):
        for raw in pattern.findall(path.read_text(encoding="utf-8")):
            target = raw.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (path.parent / target).resolve().exists():
                add_error(errors, path, f"内部链接不存在：{raw}")


def main():
    errors = []
    validate_privacy(errors)
    validate_resources(errors)
    validate_quality(errors)
    validate_links(errors)
    if errors:
        print("Publication gate failed:", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("Publication gate passed: privacy, rights, metadata, quality, and internal links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
