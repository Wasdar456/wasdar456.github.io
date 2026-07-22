"""Build the note navigation directly from folders under docs/notes."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
NOTES = ROOT / "docs" / "notes"
FOLDER_TITLES = {
    "cpp": "C++",
    "vla": "VLA 八股",
}


def _page_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        try:
            _, raw, _ = text.split("---\n", 2)
            title = (yaml.safe_load(raw) or {}).get("title")
            if title:
                return str(title)
        except (ValueError, yaml.YAMLError):
            pass
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if match:
        return match.group(1)
    return re.sub(r"^\d+[._ -]*", "", path.stem).replace("_", " ")


def _folder_nav(folder: Path):
    pages = []
    for path in sorted(folder.rglob("*.md"), key=lambda item: item.as_posix().lower()):
        relative = path.relative_to(ROOT / "docs").as_posix()
        pages.append({_page_title(path): relative})
    return pages


def on_config(config):
    note_groups = []
    if NOTES.exists():
        for folder in sorted(item for item in NOTES.iterdir() if item.is_dir()):
            pages = _folder_nav(folder)
            if pages:
                note_groups.append({FOLDER_TITLES.get(folder.name, folder.name): pages})

    nav = [{"首页": "index.md"}]
    if note_groups:
        nav.append({"笔记": note_groups})
    if (ROOT / "docs" / "resources" / "index.md").exists():
        nav.append({"资料": "resources/index.md"})
    config["nav"] = nav
    return config
