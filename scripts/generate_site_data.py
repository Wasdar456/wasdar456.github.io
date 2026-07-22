#!/usr/bin/env python3
"""Generate the public download page from data/resources.yml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "resources.yml"
OUTPUT = ROOT / "docs" / "resources" / "index.md"


def render() -> str:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    resources = [item for item in manifest.get("resources", []) if item.get("approved")]
    lines = [
        "---\n",
        "title: 附件下载\n",
        "generated: true\n",
        "---\n\n",
        "# 附件下载\n\n",
        "这里仅放 PDF、PPT、压缩包等适合单独下载的大附件。",
        "Markdown 笔记、图片和源码都跟随对应课程笔记存放。\n\n",
    ]
    if not resources:
        lines.append("暂无公开附件。\n")
    current_course = None
    current_chapter = None
    for item in resources:
        if item["course"] != current_course:
            current_course = item["course"]
            current_chapter = None
            lines.append(f'## {current_course}\n\n')
        if item["chapter"] != current_chapter:
            current_chapter = item["chapter"]
            lines.append(f'### {current_chapter}\n\n')
        lines.append(
            f'- [{item["title"]}]({item["asset_url"]}) '
            f'`{item["file_type"]}` · {item["size"]}\n'
            f'  <small>来源：{item["source"]}；公开依据：{item["rights_basis"]}</small>\n\n'
        )
    lines.extend([
        "\n---\n\n",
        "这些大附件存放在 [learning-resources Releases]",
        "(https://github.com/Wasdar456/learning-resources/releases)；",
        "普通学习笔记不需要上传到那里。\n",
    ])
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
