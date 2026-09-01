# Wasdar456 Notes

[wasdar456.github.io](https://wasdar456.github.io/) 的 MkDocs 源码。公开内容只保留个人复习笔记和已审核资料。

## 图形维护面板

macOS 双击仓库根目录的 `start-dashboard.command`，会打开只在本机运行的网站维护面板。面板可以：

- 查看分支、同步状态、最近提交和所有本地改动；
- 从 GitHub 更新、检查内容、严格编译和启动本地预览；
- 勾选要提交的文件，填写说明后提交或提交并推送；
- 在存在未提交改动时阻止更新，避免把正在写的笔记混入拉取操作。

也可以从终端启动：

```bash
.venv/bin/python scripts/control_panel.py
```

维护面板只绑定 `127.0.0.1`，不会部署到公开网站，也不会提供任意命令执行入口。

## 日常写笔记

为了便于多台电脑同步，日常直接编辑 `docs/notes/课程名/` 中的 Markdown、图片、小型源码和公开附件。写完使用：

```powershell
.\scripts\publish.ps1 -Message "notes: update"
```

`scripts/import_notes.py` 只用于第一次把旧笔记目录迁入本站，不作为长期双份同步工具。

例如源文件可以自由组织为：

```text
数据结构/
└── 第一章/
    ├── 第一章.md
    ├── images/
    ├── code/
    └── files/                 # 不超过 20 MiB 的公开下载附件
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

短代码直接写 Markdown 代码块；完整 `.cpp`、`.py` 等源码放在笔记旁边的 `code/`。不超过 20 MiB 的公开 PDF、PPT、Word、压缩包等放进对应章节的 `files/`，网站会自动生成下载入口；更大的文件使用 [learning-resources Releases](https://github.com/Wasdar456/learning-resources/releases)。
