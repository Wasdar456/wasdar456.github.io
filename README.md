# Wasdar456 Notes

[wasdar456.github.io](https://wasdar456.github.io/) 的 MkDocs 源码。公开内容只保留个人复习笔记和已审核资料。

## 日常写笔记

为了便于多台电脑同步，日常直接编辑 `docs/notes/课程名/` 中的 Markdown、图片和小型源码。写完使用：

```powershell
.\scripts\publish.ps1 -Message "notes: update"
```

`scripts/import_notes.py` 只用于第一次把旧笔记目录迁入本站，不作为长期双份同步工具。

例如源文件可以自由组织为：

```text
数据结构/
└── 第一章/
    ├── 第一章.md
    ├── 1.1例四.png
    └── max_subarray.cpp
```

新增内容会自动出现在“笔记”导航里，无需手改 `mkdocs.yml`。页面标题依次读取 YAML front matter 的 `title`、第一个一级标题、文件名。

更完整的写作、预览和上传方法见网站中的 [`docs/guide.md`](docs/guide.md)。

## 本地预览

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/generate_site_data.py
python scripts/prepublish_check.py
mkdocs serve
```

提交前运行：

```bash
python scripts/generate_site_data.py --check
python scripts/prepublish_check.py
mkdocs build --strict
```

短代码直接写 Markdown 代码块；完整 `.cpp`、`.py` 等源码放在笔记旁边。只有 PDF、PPT、Word、压缩包等大附件才使用 [learning-resources Releases](https://github.com/Wasdar456/learning-resources/releases)。
