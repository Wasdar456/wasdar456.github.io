"""Build the note navigation from the writer's existing folder structure."""

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
            metadata = yaml.safe_load(raw) or {}
            title = metadata.get("title") if isinstance(metadata, dict) else None
            if title:
                return str(title)
        except (ValueError, yaml.YAMLError):
            pass
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if match:
        return match.group(1)
    return re.sub(r"^\d+[._ -]*", "", path.stem).replace("_", " ")


def _folder_title(path: Path) -> str:
    return FOLDER_TITLES.get(
        path.name,
        re.sub(r"^\d+[._ -]*", "", path.name).replace("_", " "),
    )


def _folder_nav(folder: Path):
    """Mirror folders recursively; Markdown content never needs restructuring."""
    pages = []
    markdown_files = sorted(
        (path for path in folder.glob("*.md") if path.name.lower() != "index.md"),
        key=lambda item: item.name.lower(),
    )
    index_page = folder / "index.md"
    if index_page.exists():
        relative = index_page.relative_to(ROOT / "docs").as_posix()
        pages.append({_page_title(index_page): relative})
    for path in markdown_files:
        relative = path.relative_to(ROOT / "docs").as_posix()
        pages.append({_page_title(path): relative})
    for child in sorted(
        (path for path in folder.iterdir() if path.is_dir()),
        key=lambda item: item.name.lower(),
    ):
        child_pages = _folder_nav(child)
        if child_pages:
            pages.append({_folder_title(child): child_pages})
    return pages


def on_config(config):
    note_groups = []
    if NOTES.exists():
        for folder in sorted(
            (item for item in NOTES.iterdir() if item.is_dir()),
            key=lambda item: item.name.lower(),
        ):
            pages = _folder_nav(folder)
            if pages:
                note_groups.append({_folder_title(folder): pages})

    nav = [{"首页": "index.md"}]
    if note_groups:
        nav.append({"笔记": note_groups})
    if (ROOT / "docs" / "guide.md").exists():
        nav.append({"怎么写与发布": "guide.md"})
    if (ROOT / "docs" / "resources" / "index.md").exists():
        nav.append({"附件下载": "resources/index.md"})
    config["nav"] = nav
    return config
