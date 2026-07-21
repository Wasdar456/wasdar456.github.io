"""Build the primary navigation from the reviewed course and paper manifests."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent


def _load(name):
    with (ROOT / "data" / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def on_config(config):
    courses = _load("courses.yml")["courses"]
    papers = _load("papers.yml")["papers"]

    subject_order = ["数学", "物理", "编程", "人工智能"]
    subject_nav = []
    for subject in subject_order:
        entries = []
        for course in (item for item in courses if item["subject"] == subject):
            pages = [{"课程导航": course["index"]}]
            pages.extend({note["title"]: note["path"]} for note in course["published_notes"])
            pages.append({"课件文件库": course["resources_page"]})
            entries.append({course["title"]: pages})
        subject_nav.append({subject: entries})

    topic_order = ["深度学习", "强化学习", "VLA / Robot Learning", "模型压缩与推理加速"]
    topic_indexes = {
        "深度学习": "papers/deep-learning/index.md",
        "强化学习": "papers/reinforcement-learning/index.md",
        "VLA / Robot Learning": "papers/vla/index.md",
        "模型压缩与推理加速": "papers/model-efficiency/index.md",
    }
    paper_nav = [{"板块说明": "papers/index.md"}]
    for topic in topic_order:
        pages = [{"方向导航": topic_indexes[topic]}]
        pages.extend({paper["short_title"]: paper["path"]} for paper in papers if paper["topic"] == topic)
        paper_nav.append({topic: pages})

    config["nav"] = [
        {"首页": "index.md"},
        {"学习地图": "knowledge-map.md"},
        *subject_nav,
        {"论文精读": paper_nav},
        {"复现记录": "reproductions/index.md"},
        {"全站课程目录": "generated/course-catalog.md"},
        {"资源总目录": "generated/resource-catalog.md"},
        {"学习进度": "progress.md"},
        {"错误与未解决问题": [
            {"错误簿": "mistakes.md"},
            {"未解决问题": "questions.md"},
        ]},
        {"写作模板": [
            {"课程笔记模板": "writing-guides/course-note.md"},
            {"论文精读模板": "writing-guides/paper-review.md"},
            {"复现记录模板": "writing-guides/reproduction.md"},
        ]},
        {"关于": "about.md"},
    ]
    return config
