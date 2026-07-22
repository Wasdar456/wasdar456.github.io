# Wasdar456 Notes

[wasdar456.github.io](https://wasdar456.github.io/) 的 MkDocs 源码。公开内容只保留个人复习笔记和已审核资料。

## 添加笔记

把一个 Markdown 文件夹放进 `docs/notes/`：

```text
docs/notes/
└── new-course/
    ├── 01-first-note.md
    └── 02-second-note.md
```

提交后会自动出现在“笔记”导航里，无需手改 `mkdocs.yml`。页面标题依次读取 YAML front matter 的 `title`、第一个一级标题、文件名。

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

PDF、PPT、Word 等附件不提交到本站 Git 历史。通过公开授权与隐私检查后，上传到 [learning-resources Releases](https://github.com/Wasdar456/learning-resources/releases)，再登记到 `data/resources.yml`。
