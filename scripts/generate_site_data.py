#!/usr/bin/env python3
"""Generate reviewable navigation/status pages from the canonical manifests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "data"


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def frontmatter(title: str) -> str:
    return f"---\ntitle: {title}\ngenerated: true\n---\n\n"


def course_catalog(courses):
    lines = [
        frontmatter("全站课程目录"),
        "# 全站课程目录\n\n",
        "本页由 `data/courses.yml` 自动生成。进度是公开笔记的整理进度，不等同于课程成绩或最终掌握程度。\n\n",
        "| 学科 | 课程 | 正式笔记 | 待整理主题 | 公开进度 |\n",
        "|---|---|---:|---:|---:|\n",
    ]
    for course in courses:
        lines.append(
            f'| {course["subject"]} | [{course["title"]}](../{course["index"]}) | '
            f'{len(course["published_notes"])} | {len(course["pending_chapters"])} | {course["progress"]}% |\n'
        )
    lines.extend([
        "\n## 状态口径\n\n",
        "- **正式笔记**：已达到本站详细笔记模板的最低要求，并进入持续校对。\n",
        "- **待整理主题**：只在课程导航展示，不生成低质量占位文章。\n",
        "- **公开进度**：按公开页面覆盖程度估计；私有研究与未公开作业永远不计入。\n",
    ])
    return "".join(lines)


def resource_catalog(resources):
    lines = [
        frontmatter("资源总目录"),
        "# 资源总目录\n\n",
        "资源数据由 `data/resources.yml` 统一驱动。首版没有通过授权白名单的附件，因此不上传第三方课件。\n\n",
        "| 课程 | 章节 | 标题 | 类型 | 大小 | 来源 | 授权依据 | 版本 / 校验值 | 下载 |\n",
        "|---|---|---|---|---:|---|---|---|---|\n",
    ]
    approved = [item for item in resources if item.get("approved")]
    if not approved:
        lines.append("| — | — | 暂无通过公开审核的附件 | — | — | — | — | — | — |\n")
    for item in approved:
        checksum = item["checksum"]
        short_checksum = f'{checksum[:15]}…' if len(checksum) > 16 else checksum
        lines.append(
            f'| {item["course"]} | {item["chapter"]} | {item["title"]} | {item["file_type"]} | '
            f'{item["size"]} | {item["source"]} | {item["rights_basis"]} | `{short_checksum}` | '
            f'[下载]({item["asset_url"]}) |\n'
        )
    lines.extend([
        "\n!!! warning \"授权优先\"\n",
        "    教师课件、教材、试卷、答案和课程平台下载件，除非存在明确的再分发许可，否则只保留本地；本站最多给出官方公开页面链接。\n",
        "\n附件仓库：[Wasdar456/learning-resources](https://github.com/Wasdar456/learning-resources)。\n",
    ])
    return "".join(lines)


def course_resource_page(course, approved_resources):
    rows = [item for item in approved_resources if item["course"] == course["id"]]
    lines = [
        frontmatter(f'{course["title"]} · 课件文件库'),
        f'# {course["title"]} · 课件文件库\n\n',
        "本页只列出已经过授权、隐私和校验值审核的公开附件。文件通过课程级 GitHub Release 提供，不进入 Pages 的 Git 历史。\n\n",
        "| 章节 | 文件名 | 类型 | 大小 | 来源 | 授权状态 | 版本 / 校验值 | 下载 |\n",
        "|---|---|---|---:|---|---|---|---|\n",
    ]
    if not rows:
        lines.append("| — | 暂无通过公开审核的附件 | — | — | — | 待授权清单 | — | — |\n")
    for item in rows:
        lines.append(
            f'| {item["chapter"]} | {item["title"]} | {item["file_type"]} | {item["size"]} | '
            f'{item["source"]} | 已批准：{item["rights_basis"]} | `{item["checksum"][:15]}…` | '
            f'[下载]({item["asset_url"]}) |\n'
        )
    lines.extend([
        "\n## 审核规则\n\n",
        "1. 只接受本人原创、公共领域、开放许可证或已经取得明确再分发授权的文件。\n",
        "2. 每个文件必须登记来源、授权依据、大小和 SHA-256 校验值。\n",
        "3. 未授权教师课件和教材不上传；可链接其官方公开地址。\n",
        "4. 上传前还需通过隐私扫描，确认不含真实姓名、学号、凭据和私有研究内容。\n",
        "\n查看[全站资源总目录](../../generated/resource-catalog.md)。\n",
    ])
    return "".join(lines)


def outputs():
    courses = load_yaml(DATA / "courses.yml")["courses"]
    resources = load_yaml(DATA / "resources.yml")["resources"]
    approved = [item for item in resources if item.get("approved")]
    generated = {
        DOCS / "generated" / "course-catalog.md": course_catalog(courses),
        DOCS / "generated" / "resource-catalog.md": resource_catalog(resources),
    }
    for course in courses:
        generated[DOCS / course["resources_page"]] = course_resource_page(course, approved)
    return generated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args()
    stale = []
    for path, content in outputs().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if stale:
        print("Generated files are stale: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

