---
title: 怎么写、预览、上传和管理附件
---

# 怎么写、预览、上传和管理附件

这份说明从第一次使用开始写。平时如果忘记文件放哪里、命令怎么运行，回到这一页照着操作即可。

## 最短版：日常只需要这几步

开始写之前：

```powershell
cd D:\Study\homepage
git pull --ff-only
```

写完后先检查和预览：

```powershell
.\scripts\publish.ps1 -Message "notes: update" -NoPush
.\.venv\Scripts\python.exe -m mkdocs serve
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

确认无误后按 `Ctrl+C` 停止预览，再上传：

```powershell
.\scripts\publish.ps1 -Message "notes: update"
```

从现在开始，公开笔记只编辑：

```text
D:\Study\homepage\docs\notes
```

不要编辑 `site/`，也不要继续编辑 `_archive` 里的迁移前备份。

## 1. 第一次使用或换一台电脑

### 1.1 克隆唯一的正式仓库

新电脑上打开 PowerShell：

```powershell
cd D:\Study
git clone ssh://git@ssh.github.com:443/Wasdar456/wasdar456.github.io.git homepage
cd D:\Study\homepage
```

最后一行执行后，PowerShell 当前目录应该是：

```text
D:\Study\homepage
```

可以用下面的命令确认：

```powershell
Get-Location
git status -sb
```

正常情况下会看到 `main...origin/main`。`homepage` 才是以后使用的正式主页仓库。

### 1.2 第一次创建本地环境

执行：

```powershell
.\scripts\publish.ps1 -NoPush
```

如果 `.venv` 不存在，脚本会自动：

1. 创建 `D:\Study\homepage\.venv`。
2. 安装网站构建依赖。
3. 生成附件下载页。
4. 检查隐私、链接和附件。
5. 构建一次网站。

`.venv` 只服务于这台电脑，不会上传 GitHub。换电脑后在新电脑重新运行一次即可。

### 1.3 哪些目录不能编辑

- `site/`：MkDocs 自动生成的网页成品，随时可以重建。
- `.venv/`：本机 Python 环境。
- `.git/`：Git 内部数据。
- `D:\Study\_archive`：迁移前备份，只用于找回旧文件。

真正需要编辑的是 `docs/`，尤其是 `docs/notes/`。

## 2. 每次开始写笔记

先把 GitHub 上其他电脑已经上传的内容拉下来：

```powershell
cd D:\Study\homepage
git pull --ff-only
```

`git pull --ff-only` 只接受清晰的快进同步，不会擅自生成合并提交。

多电脑使用时遵守两条规则：

1. 开始写之前先 pull。
2. 一台电脑写完并上传后，另一台电脑再继续写。

尽量不要让两台电脑同时长期修改同一个 Markdown 文件。

## 3. 新建课程和章节

文件夹层级可以按自己的笔记习惯组织，不需要套固定模板。例如：

```text
docs/notes/
└── CS336/
    └── Lecture3/
        ├── Lecture3.md
        ├── images/
        ├── code/
        └── files/
```

四类内容的用途：

- `Lecture3.md`：笔记正文。
- `images/`：需要在网页中显示的图片。
- `code/`：适合查看或下载的小型示例源码。
- `files/`：PDF、PPT、Word、压缩包、Notebook 等公开下载附件。

文件夹名称不必与这个示例完全一致。网站会递归读取 `docs/notes`，自动生成左侧导航，不需要修改 `mkdocs.yml`。

### 3.1 页面标题

推荐在 Markdown 最上方写：

```yaml
---
title: CS336 Lecture 3：架构与训练计算
---
```

注意：

- 必须是小写 `title:`。
- `---` 需要单独占一行。
- 标题可以使用中文、英文和编号。

如果不写 `title`，网站依次使用：

1. Markdown 中第一个一级标题。
2. Markdown 文件名。

推荐示例：

- `第一章：数据结构与算法基础`
- `第二章：线性表`
- `CS336 Lecture 2：Einops and FLOPs`

## 4. 图片和代码怎么放

### 4.1 图片

推荐放进本章的 `images/`：

```text
Lecture3/
├── Lecture3.md
└── images/
    └── compute-graph.png
```

Markdown 写：

```markdown
![计算图](images/compute-graph.png)
```

图片也可以放在 Markdown 旁边，只要使用正确的相对路径即可。

### 4.2 页面内代码

短代码直接使用 Markdown 代码块：

````markdown
```python
import torch

x = torch.randn(2, 3)
print(x.shape)
```
````

网页会显示语法高亮和复制按钮。

### 4.3 小型完整源码

需要单独查看或运行的源码放进 `code/`：

```text
Lecture3/
├── Lecture3.md
└── code/
    └── matmul.py
```

Markdown 写：

```markdown
[查看 matmul.py](code/matmul.py)
```

`code/` 适合与笔记直接相关的小型演示程序，不适合整套课程作业、虚拟环境、编译产物或模型。

## 5. 写完后检查和本地预览

先运行：

```powershell
cd D:\Study\homepage
.\scripts\publish.ps1 -Message "notes: update CS336 lecture 3" -NoPush
```

`-NoPush` 会：

- 更新全站附件下载页。
- 检查附件大小和类型。
- 检查 Markdown 图片及相对链接。
- 检查可能的隐私信息、密钥和危险文件。
- 严格构建网站。
- 列出与本地最新提交不同的全部文件。

`-NoPush` 不会：

- 创建 Git 提交。
- 上传 GitHub。
- 修改远端网页。

检查通过后启动预览：

```powershell
.\.venv\Scripts\python.exe -m mkdocs serve
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

预览服务运行时继续保存 Markdown，浏览器通常会自动刷新。检查完成后回到 PowerShell，按：

```text
Ctrl+C
```

停止预览。

### 5.1 怎样阅读待发布清单

脚本会显示类似：

```text
 M docs/index.md
 M docs/guide.md
?? docs/notes/CS336/Lecture3/
```

含义：

- `M`：现有文件被修改。
- `??`：新文件或新文件夹尚未提交。
- `D`：文件被删除。
- `R`：Git 识别为重命名。

确认清单只包含准备公开的内容后，再执行正式上传。

## 6. 确认后上传

执行：

```powershell
.\scripts\publish.ps1 -Message "notes: update CS336 lecture 3"
```

脚本会再次检查和构建，然后：

1. 收集仓库内所有有效改动。
2. 打印将进入提交的文件清单。
3. 创建 Git 提交。
4. 推送到 GitHub 的 `main`。

它不再只上传 `docs/notes`，因此首页、指南、附件、脚本、配置、重命名和删除都会被正确包含。

### 6.1 提交信息怎么写

提交信息不影响网站功能，但应当让以后能看懂这次改了什么。

推荐：

```powershell
.\scripts\publish.ps1 -Message "notes: update data structures chapter 2"
.\scripts\publish.ps1 -Message "notes: add CS336 lecture 3"
.\scripts\publish.ps1 -Message "site: update homepage"
.\scripts\publish.ps1 -Message "resources: add lecture 3 slides"
```

### 6.2 上传后怎样确认

执行：

```powershell
git status -sb
git log -1 --oneline
```

正常情况下：

- 第一行显示 `main...origin/main`。
- 后面没有 `M`、`??` 等待提交文件。
- `git log` 的第一条是刚才填写的提交信息。

GitHub Pages 部署通常需要几分钟。随后检查：

- [个人主页](https://wasdar456.github.io/)
- [附件下载](https://wasdar456.github.io/resources/)

## 7. 添加不超过 20 MiB 的可下载附件

### 7.1 放入 `files/`

例如：

```text
docs/notes/CS336/Lecture3/
├── Lecture3.md
└── files/
    ├── lecture3-slides.pdf
    └── exercise.zip
```

放入 `files/` 表示确认该文件允许公开和再分发。

支持的常见类型包括：

- PDF、DOC、DOCX、PPT、PPTX、XLS、XLSX。
- ZIP、7z、RAR、TAR、GZ。
- CSV、JSON、IPYNB、TXT。

可执行程序、安装包、密钥和环境文件会被阻止。

### 7.2 在笔记中添加链接

```markdown
[下载 Lecture 3 PDF](files/lecture3-slides.pdf){ download }

[下载练习代码](files/exercise.zip){ download }
```

PDF 链接不加 `{ download }` 时，浏览器通常会直接打开 PDF；加上后会优先下载。

文件名可以使用中文，但更推荐稳定、简短的名称：

- `lecture3-slides.pdf`
- `数据结构-第二章-练习.pdf`
- `exercise-code.zip`

不要频繁修改文件名。重命名后必须同步修改 Markdown 链接，否则发布检查会报告“内部链接不存在”。

### 7.3 完整上传流程

1. 把文件复制进对应章节的 `files/`。
2. 在 Markdown 中写相对链接。
3. 运行：

   ```powershell
   .\scripts\publish.ps1 -NoPush
   ```

4. 启动本地预览并点击下载链接：

   ```powershell
   .\.venv\Scripts\python.exe -m mkdocs serve
   ```

5. 确认附件页也出现了该文件。
6. 停止预览并正式上传：

   ```powershell
   .\scripts\publish.ps1 -Message "resources: add lecture 3 files"
   ```

全站附件页会自动扫描所有章节的 `files/`，根据目录识别课程和章节，并显示文件名、类型、大小和直接下载链接。不需要为站内附件手写 SHA 或大小。

## 8. 超过 20 MiB 的大文件

大文件不要放进 `homepage`。使用：

[Wasdar456/learning-resources Releases](https://github.com/Wasdar456/learning-resources/releases)

GitHub 普通仓库在单文件超过 50 MiB 时警告，超过 100 MiB 时阻止；本项目使用更保守的 20 MiB 限制，避免多电脑 clone 和 pull 越来越慢。

### 8.1 用网页上传 Release

1. 打开 `learning-resources` 的 Releases 页面。
2. 点击创建新 Release。
3. 填写一个稳定的 tag，例如 `cs336-lecture3-2026.1`。
4. 填写标题。
5. 把附件拖入上传区域。
6. 发布 Release。
7. 在附件名称上复制下载链接。

单个 Release 里可以放多个相关文件。

### 8.2 登记到主页附件页

编辑：

```text
D:\Study\homepage\data\resources.yml
```

增加一项：

```yaml
- course: CS336
  chapter: Lecture 3
  title: Lecture 3 补充资料
  asset_url: https://github.com/Wasdar456/learning-resources/releases/download/对应-tag/文件名.pdf
  file_type: PDF
  size: 35.0 MiB
  source: 本人整理
  rights_basis: 本人整理并批准公开
  checksum: sha256:这里填写64位小写SHA256
  approved: true
```

计算 SHA256：

```powershell
(Get-FileHash -Algorithm SHA256 -LiteralPath "D:\文件位置\文件名.pdf").Hash.ToLower()
```

把结果放在 `sha256:` 后面。然后运行：

```powershell
.\scripts\publish.ps1 -NoPush
```

附件页会同时保留：

- `files/` 中的站内直接下载文件。
- Releases 中的大文件和历史资料。

官方限制说明：

- [GitHub 普通仓库文件限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [GitHub Releases 说明](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## 9. 哪些内容不要公开

- 没有再分发授权的教材、教师课件、课程平台下载件。
- 含姓名、学号、手机号、成绩或私人实验数据的文件。
- 密钥、令牌、密码、`.env`、证书和私钥。
- 数据集、模型权重、checkpoint、训练日志。
- `.venv`、编译目录和生成产物。
- 完整的课程作业仓库，尤其是可能违反课程规定的公开答案。

发布脚本能发现一部分风险，但不能替代你对版权和课程规定的判断。

## 10. CS336 代码、资料和笔记分别放哪里

### 10.1 公开学习笔记

```text
D:\Study\homepage\docs\notes\CS336
```

这里放：

- 课程内容总结。
- 自己的推导和理解。
- 配套图片。
- 小型演示代码。
- 允许公开的小附件。

### 10.2 完整作业实现

```text
D:\Study\CS336\assignments
```

完整 Assignment 是独立软件工程，不要复制进主页。

### 10.3 数据和实验输出

```text
D:\Study\CS336\data
D:\Study\CS336\outputs
```

这里放：

- 数据集。
- checkpoint。
- 模型权重。
- 日志。
- 大型实验输出。

这些内容不通过主页仓库同步。换电脑时重新下载或使用专门的云存储。

## 11. 多电脑工作流

电脑 A 开始前：

```powershell
cd D:\Study\homepage
git pull --ff-only
```

电脑 A 写完后：

```powershell
.\scripts\publish.ps1 -Message "notes: update"
```

确认上传成功后，电脑 B 再执行：

```powershell
cd D:\Study\homepage
git pull --ff-only
```

### 11.1 判断当前同步状态

```powershell
git status -sb
```

常见情况：

- 只有 `## main...origin/main`：本地文件和本地已知远端一致。
- 后面有 `M` 或 `??`：存在尚未提交的本地修改。
- 显示 `[ahead 1]`：有一个本地提交尚未推送。
- 显示 `[behind 1]`：远端有一个新提交尚未拉取。
- 同时 ahead 和 behind：两边都发生了提交，需要先处理分叉。

不要在两台电脑上同时修改同一篇笔记后直接互相覆盖。

## 12. 常见错误

### 12.1 首页改了但 GitHub 没变化

先看：

```powershell
git status -sb
git log -1 --oneline
```

新版发布脚本会使用 `git add -A`，首页、指南和配置也会进入提交。如果 `docs/index.md` 仍显示 `M`，说明还没有成功运行正式发布。

### 12.2 `No changes to publish`

含义：检查和构建成功，但 Git 没发现需要提交的变化。

确认是否编辑了正确目录：

```powershell
Get-Location
git status -sb
```

正确位置应是 `D:\Study\homepage`。

### 12.3 `non-fast-forward`

含义：GitHub 上有本地没有的提交，通常来自另一台电脑。

不要连续重复 push。先保留当前文件并检查：

```powershell
git status -sb
git log --oneline --decorate -5
```

如果当前没有未提交文件，再执行：

```powershell
git pull --rebase origin main
```

若出现冲突，不要删除文件或强制 push；先逐个确认冲突内容。

### 12.4 附件超过 20 MiB

脚本会显示文件名和大小，并停止发布。把文件从 `files/` 移出，改用 `learning-resources` Release，再登记到 `data/resources.yml`。

### 12.5 图片或附件链接不存在

检查：

- 文件名大小写是否一致。
- 文件是否确实在 Markdown 相对路径指向的位置。
- 重命名文件后是否更新了 Markdown。
- 路径中是否误用了绝对盘符。

推荐始终使用相对路径。

### 12.6 检测到隐私信息或密钥

发布立即停止。根据提示打开对应文件，删除或匿名化信息，再重新运行 `-NoPush`。

不要为了绕过检查而关闭隐私规则。

### 12.7 本地预览端口被占用

换一个端口：

```powershell
.\.venv\Scripts\python.exe -m mkdocs serve -a 127.0.0.1:8001
```

然后打开：

```text
http://127.0.0.1:8001/
```

### 12.8 GitHub Pages 还没更新

先确认上传是否真的完成：

```powershell
git status -sb
git log -1 --oneline
```

再打开仓库的 Actions 页面查看部署。Pages 通常需要几分钟，不要因为网页暂时没刷新就重复提交相同内容。

### 12.9 push 失败，但已经创建了 commit

脚本会明确显示：

```text
Upload failed. The commit is safe in the local repository but is not on GitHub.
```

此时内容没有丢失，只是提交还在本地。检查：

```powershell
git status -sb
git log -1 --oneline
```

如果显示 `[ahead 1]`，说明本地比远端多一个提交。解决网络或同步问题后，只需：

```powershell
git push origin main
```

不需要重新编辑，也不要反复生成相同提交。

## 最后只记住三件事

1. 开始前：

   ```powershell
   git pull --ff-only
   ```

2. 预览前：

   ```powershell
   .\scripts\publish.ps1 -NoPush
   ```

3. 确认后：

   ```powershell
   .\scripts\publish.ps1 -Message "notes: update"
   ```
