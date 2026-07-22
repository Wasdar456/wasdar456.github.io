---
title: 文件放哪里，以及怎样在多台电脑上写作
---

# 文件放哪里，以及怎样在多台电脑上写作

## 先记住：以后只保留一份公开笔记

如果只在一台电脑写作，可以在别处写完再复制到网站仓库。但你准备在多台电脑之间使用，所以更推荐把**公开笔记的 Markdown 源文件直接放在主页仓库中编辑**，不要长期维护两份。

假设主页仓库克隆在 `D:\Study\homepage`，数据结构笔记就放在：

```text
D:\Study\homepage\docs\notes\数据结构\第一章\第一章.md
```

以后应当编辑上面这份文件，而不是同时修改 `D:\Study\数据结构\第一章\第一章.md`。旧的 `D:\Study\数据结构` 只用于第一次迁移；确认网站仓库内的文件和图片都完整后，可以将旧目录改名为“旧备份”，避免误编辑。

“笔记是源文件，网站只是展示器”的准确含义是：

- 你编辑的是 `docs/notes` 里的 Markdown、图片和小型源码。
- GitHub 保存这些源文件，并负责多电脑同步和历史版本。
- MkDocs 根据源文件生成网页。
- `site/` 是自动生成的网页成品，**不要编辑、不要上传、不要同步**。

## 总体目录设计

```text
D:\Study\
├── homepage\                       # 你的主页 Git 仓库，公开、跨电脑同步
│   ├── docs\notes\
│   │   ├── 数据结构\
│   │   │   └── 第一章\
│   │   │       ├── 第一章.md
│   │   │       ├── 1.1例四.png
│   │   │       └── code\           # 可选：与本章配套的小型完整源码
│   │   └── CS336\                   # 只放公开学习笔记，不放整套作业工程
│   ├── data\resources.yml          # 大附件下载清单
│   ├── scripts\
│   └── site\                        # 自动生成，忽略
│
├── CS336\                           # CS336 学习与作业区，不属于主页
│   ├── assignments\                 # 官方作业和你的实现
│   ├── private-notes\               # 草稿、私人思考；不自动公开
│   ├── data\                        # 可选的共享大数据缓存，不进 Git
│   └── outputs\                     # checkpoint、日志、实验输出，不进 Git
│
└── learning-resources\              # 可选：主页大附件仓库
```

## 主页仓库里可以放什么

### Markdown 和图片

每门课程放一个文件夹，内部章节层级由你决定，网站会照着读取：

```text
docs\notes\数据结构\
├── 第一章\
│   ├── 第一章.md
│   ├── 1.1例四.png
│   └── 1.3算法四.png
└── 第二章\
    └── 第二章.md
```

图片放在 Markdown 旁边，并使用相对路径：

```markdown
![复杂度示意](./1.2复杂度渐进表示.png)
```

### 标题

每篇 Markdown 最上方可以写：

```yaml
---
title: 第一章：数据结构与算法基础
---
```

必须是小写 `title:`，冒号不能省略。推荐使用“编号：主题”，例如 `第二章：线性表` 或 `Lecture 01：Tokenization`。

### 短代码

讲解某个算法时，直接写 Markdown 代码块：

````markdown
```cpp
int main() {
    return 0;
}
```
````

它会直接显示在网页上，并支持高亮和复制。

### 小型完整源码

如果某段程序需要单独编译，可以放在章节旁边：

```text
第一章\
├── 第一章.md
└── code\
    ├── max_subarray.cpp
    └── CMakeLists.txt
```

笔记中写：

```markdown
[查看完整代码](./code/max_subarray.cpp)
```

适合放在主页仓库中的源码应当体积小，并且直接服务于笔记。不要把 `.venv`、编译产物、模型权重、数据集或整套课程作业工程放进主页。

## PDF、PPT、Word、ZIP 怎么放

### 可以直接放在笔记旁边的情况

自己制作、体积很小、确实需要和某篇笔记一起浏览的单个文件可以放在课程目录中，但不建议把主页当网盘。

### 推荐放到 learning-resources 的情况

以下文件放到 `learning-resources` 的 GitHub Releases：

- 自己整理并允许公开的 PDF 讲义。
- 自己制作的试卷、答案、PPT。
- 需要提供下载但不适合进入主页 Git 历史的压缩包。
- 体积较大的附件。

上传 Release 后，在主页的 `data/resources.yml` 登记下载链接，网页会自动按课程和章节列出。

### 不要上传的内容

- 没有再分发授权的教材、教师课件、课程平台下载件。
- 含姓名、学号、手机号、成绩或私人实验数据的文件。
- 数据集、模型权重、checkpoint、`.venv`、编译目录。

## CS336 作业应该放哪里

整套 CS336 Assignment 是可运行的软件工程，不是网页笔记，所以放在：

```text
D:\Study\CS336\assignments\assignment1-basics
```

Assignment 1 的常见结构是：

```text
assignment1-basics\
├── cs336_basics\             # 你的主要实现代码
├── tests\                    # 官方测试和 adapters.py
├── data\                     # TinyStories/OWT；下载后留本机，不推 Git
├── cs336_assignment1_basics.pdf
├── pyproject.toml
└── uv.lock
```

做作业时主要修改 `cs336_basics`，并按照题目要求连接 `tests/adapters.py`。不要把整个 `assignment1-basics` 复制进主页；可以另外在 `homepage/docs/notes/CS336` 写公开总结，再用少量代码块解释实现。

数据集放在作业 README 指定的 `assignment1-basics/data`；模型、checkpoint 和运行日志放在被 `.gitignore` 忽略的目录，或者 `D:\Study\CS336\outputs`。这些文件通常很大，换电脑时重新下载或从云存储取得，不通过 GitHub 源码仓库同步。

## 多台电脑怎样同步主页笔记

### 每台电脑只做一次

```powershell
cd D:\Study
git clone https://github.com/Wasdar456/wasdar456.github.io.git homepage
cd .\homepage
```

### 每次开始写之前

```powershell
cd D:\Study\homepage
git pull --ff-only
```

### 写完后预览

```powershell
.\scripts\publish.ps1 -Message "notes: update data structures chapter 1" -NoPush
.\.venv\Scripts\python.exe -m mkdocs serve
```

### 确认后上传

```powershell
.\scripts\publish.ps1 -Message "notes: update data structures chapter 1"
```

上传后，另一台电脑在开始写之前再执行 `git pull --ff-only`。最重要的规则是：**开始前 pull，结束后 push；不要让两台电脑同时修改同一篇笔记而长期不上传。**

## 多台电脑怎样同步 CS336 作业代码

最稳妥的方式是：在 GitHub 上 Fork 每个 Stanford 官方 Assignment 仓库到自己的账号，然后每台电脑都克隆自己的 Fork。

```text
Stanford 官方仓库（upstream）
        ↓ 获取题目更新
你的 Fork（origin）
        ↕ push / pull
电脑 A、电脑 B
```

代码、测试适配和小型配置通过自己的 Fork 同步；`data/`、`.venv/`、checkpoint、日志不提交。若你不想公开自己的作业实现，应把个人作业仓库设为私有，并先确认课程关于公开解答的规定。

## 第一次迁移旧数据结构笔记

只有从旧目录迁移到主页仓库时才运行：

```powershell
cd D:\Study\homepage
python scripts\import_notes.py "D:\Study\数据结构"
```

迁移完成、确认文件一致后，今后直接编辑 `homepage/docs/notes/数据结构`，不再反复从旧目录导入。
