# Wasdar456 Learning Hub

这是 <https://wasdar456.github.io/> 的 MkDocs 源码仓库。站点按“学科 → 课程 → 章节 → 详细笔记”组织，重点保存经过重写、推导、校对和来源核验的学习记录。

## 本地检查

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/generate_site_data.py --check
python scripts/prepublish_check.py
mkdocs build --strict
```

如需更新课程状态或论文导航，先编辑 `data/courses.yml` 或 `data/papers.yml`，再运行：

```bash
python scripts/generate_site_data.py
```

课件附件不进入本仓库。经授权的附件由独立的 `Wasdar456/learning-resources` 仓库及其 GitHub Releases 托管。

