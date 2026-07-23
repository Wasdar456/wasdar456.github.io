#!/usr/bin/env python3
"""Generate the download page from local note attachments and external releases."""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "docs" / "notes"
MANIFEST = ROOT / "data" / "resources.yml"
OUTPUT = ROOT / "docs" / "resources" / "index.md"


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def local_resources() -> list[dict[str, str]]:
    resources: list[dict[str, str]] = []
    if not NOTES.exists():
        return resources

    for files_dir in sorted(
        (path for path in NOTES.rglob("files") if path.is_dir()),
        key=lambda path: path.as_posix().lower(),
    ):
        relative_dir = files_dir.relative_to(NOTES)
        parts = relative_dir.parts
        if not parts:
            continue
        course = parts[0]
        chapter = " / ".join(parts[1:-1]) or "其他"

        for path in sorted(
            (item for item in files_dir.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix().lower(),
        ):
            link = os.path.relpath(path, OUTPUT.parent).replace("\\", "/")
            resources.append(
                {
                    "course": course,
                    "chapter": chapter,
                    "title": path.name,
                    "asset_url": link,
                    "file_type": path.suffix.lstrip(".").upper() or "FILE",
                    "size": human_size(path.stat().st_size),
                }
            )
    return resources


def external_resources() -> list[dict[str, str]]:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    return [
        item
        for item in manifest.get("resources", [])
        if item.get("approved")
    ]


def append_grouped_resources(
    lines: list[str],
    resources: list[dict[str, str]],
    *,
    local: bool,
) -> None:
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for item in resources:
        grouped[str(item["course"])][str(item["chapter"])].append(item)

    for course in sorted(grouped, key=str.lower):
        lines.append(f"### {course}\n\n")
        for chapter in sorted(grouped[course], key=str.lower):
            lines.append(f"#### {chapter}\n\n")
            for item in sorted(
                grouped[course][chapter],
                key=lambda value: str(value["title"]).lower(),
            ):
                url = str(item["asset_url"])
                target = f"<{url}>" if local else url
                suffix = "{ download }" if local else ""
                lines.append(
                    f'- [{item["title"]}]({target}){suffix} '
                    f'`{item["file_type"]}` · {item["size"]}\n'
                )
                if not local:
                    lines.append(
                        f'  <small>来源：{item["source"]}；'
                        f'公开依据：{item["rights_basis"]}</small>\n'
                    )
            lines.append("\n")


def render() -> str:
    local = local_resources()
    external = external_resources()
    lines = [
        "---\n",
        "title: 附件下载\n",
        "generated: true\n",
        "---\n\n",
        "# 附件下载\n\n",
        "这里汇总笔记章节 `files/` 文件夹中的站内附件，以及存放在 "
        "[learning-resources Releases]"
        "(https://github.com/Wasdar456/learning-resources/releases) "
        "中的大文件。站内附件可以直接下载。\n\n",
        "## 站内附件\n\n",
    ]
    if local:
        append_grouped_resources(lines, local, local=True)
    else:
        lines.append("暂无站内附件。把公开文件放进对应章节的 `files/` 后会自动出现在这里。\n\n")

    lines.append("## Releases 大附件与历史资料\n\n")
    if external:
        append_grouped_resources(lines, external, local=False)
    else:
        lines.append("暂无 Release 附件。\n\n")

    lines.extend(
        [
            "---\n\n",
            "站内附件单文件不得超过 20 MiB。更大的公开文件请使用 "
            "[GitHub Releases]"
            "(https://github.com/Wasdar456/learning-resources/releases)。"
            "只有本人原创、已获授权或明确允许再分发的资料才能公开。\n",
        ]
    )
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            print(f"Generated file is stale: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
