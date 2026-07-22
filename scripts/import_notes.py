#!/usr/bin/env python3
"""Copy an existing note folder into the site without rewriting its contents."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "docs" / "notes"
ALLOWED_SUFFIXES = {
    ".md", ".txt", ".rst",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".java", ".js",
    ".ts", ".rs", ".go", ".m", ".sh", ".ps1",
    ".csv", ".json", ".yml", ".yaml",
}
IGNORED_NAMES = {".git", ".venv", "__pycache__", ".DS_Store", "Thumbs.db"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="原样导入 Markdown、图片和源码；不会修改笔记正文。"
    )
    parser.add_argument("source", type=Path, help="原笔记文件夹")
    parser.add_argument(
        "--name",
        help="网站中的课程名；默认使用源文件夹名称",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_dir():
        print(f"找不到笔记文件夹：{source}", file=sys.stderr)
        return 1

    course_name = args.name or source.name
    if course_name in {"", ".", ".."} or any(char in course_name for char in '<>:"/\\|?*'):
        print(f"课程名不能用于文件夹：{course_name}", file=sys.stderr)
        return 1

    destination = (NOTES / course_name).resolve()
    if NOTES.resolve() not in destination.parents:
        print("目标目录超出 docs/notes，已停止。", file=sys.stderr)
        return 1

    files = []
    skipped = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part in IGNORED_NAMES or part.startswith(".") for part in relative.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            skipped.append(relative)
            continue
        files.append((path, relative))

    if not any(path.suffix.lower() == ".md" for path, _ in files):
        print("没有找到 Markdown 文件，未导入。", file=sys.stderr)
        return 1

    for path, relative in files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    print(f"已原样导入 {len(files)} 个文件到 {destination.relative_to(ROOT)}")
    if skipped:
        print("以下大附件或未知文件未导入（请放 learning-resources）：")
        for path in skipped:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
