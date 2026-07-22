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
        "title: 资料\n",
        "generated: true\n",
        "---\n\n",
        "# 资料\n\n",
        "| 课程 | 内容 | 文件 | 大小 | 来源 / 授权 | SHA-256 |\n",
        "|---|---|---|---:|---|---|\n",
    ]
    if not resources:
        lines.append("| — | 暂无公开资料 | — | — | — | — |\n")
    for item in resources:
        checksum = str(item["checksum"]).removeprefix("sha256:")
        lines.append(
            f'| {item["course"]} | {item["chapter"]} | '
            f'[{item["title"]}]({item["asset_url"]}) ({item["file_type"]}) | '
            f'{item["size"]} | {item["source"]}；{item["rights_basis"]} | '
            f'`{checksum[:12]}…` |\n'
        )
    lines.extend([
        "\n文件存放在 [learning-resources Releases]",
        "(https://github.com/Wasdar456/learning-resources/releases)。\n",
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
