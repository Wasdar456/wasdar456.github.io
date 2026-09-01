#!/usr/bin/env python3
"""Local-only maintenance panel for the Wasdar456 Notes repository."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
PANEL_DIR = ROOT / "tools" / "control-panel"
HOST = "127.0.0.1"
DEFAULT_PORT = 8766
PREVIEW_PORT = 8765
MAX_REQUEST_SIZE = 512 * 1024


class CommandError(RuntimeError):
    """A fixed maintenance command failed."""

    def __init__(self, title: str, output: str, returncode: int = 1):
        super().__init__(output)
        self.title = title
        self.output = output
        self.returncode = returncode


def python_executable() -> str:
    candidates = [
        ROOT / ".venv" / "bin" / "python",
        ROOT / ".venv" / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def run(command: list[str], title: str, timeout: int = 180) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    output = completed.stdout.strip()
    if completed.returncode:
        raise CommandError(title, output or f"命令失败，退出码 {completed.returncode}")
    return output


def git(*args: str, title: str = "Git 操作", timeout: int = 180) -> str:
    return run(["git", *args], title, timeout)


def changed_files() -> list[dict[str, str]]:
    output = git(
        "-c",
        "core.quotepath=false",
        "status",
        "--short",
        "--untracked-files=all",
        title="读取文件状态",
    )
    files: list[dict[str, str]] = []
    labels = {
        "M": "修改",
        "A": "新增",
        "D": "删除",
        "R": "重命名",
        "C": "复制",
        "U": "冲突",
        "?": "未跟踪",
    }
    for line in output.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        display_path = line[3:]
        stage_path = display_path.rsplit(" -> ", 1)[-1]
        kind = next((labels[c] for c in code if c != " "), "变化")
        files.append(
            {
                "code": code,
                "kind": kind,
                "path": stage_path,
                "display_path": display_path,
                "staged": " " != code[0] and "?" != code[0],
            }
        )
    return files


def sync_counts() -> tuple[int, int]:
    try:
        output = git(
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
            title="读取同步状态",
        )
        ahead, behind = output.split()
        return int(ahead), int(behind)
    except (CommandError, ValueError):
        return 0, 0


def repository_snapshot() -> dict[str, object]:
    branch = git("branch", "--show-current", title="读取当前分支") or "(detached)"
    ahead, behind = sync_counts()
    latest = git(
        "log",
        "-1",
        "--date=format:%Y-%m-%d %H:%M",
        "--format=%h%x09%s%x09%ad",
        title="读取最新提交",
    )
    parts = latest.split("\t", 2)
    files = changed_files()
    return {
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "clean": not files,
        "files": files,
        "latest": {
            "hash": parts[0] if parts else "",
            "subject": parts[1] if len(parts) > 1 else "",
            "date": parts[2] if len(parts) > 2 else "",
        },
        "preview_running": PreviewProcess.running(),
        "preview_url": f"http://{HOST}:{PREVIEW_PORT}/",
        "site_url": "https://wasdar456.github.io/",
        "actions_url": "https://github.com/Wasdar456/wasdar456.github.io/actions",
    }


def validate_paths(paths: object) -> list[str]:
    if not isinstance(paths, list) or not paths:
        raise CommandError("提交文件", "请至少选择一个要提交的文件。")
    known = {item["path"] for item in changed_files()}
    selected: list[str] = []
    for raw in paths:
        if not isinstance(raw, str) or raw not in known:
            raise CommandError("提交文件", f"文件不在当前改动中：{raw}")
        resolved = (ROOT / raw).resolve(strict=False)
        if resolved != ROOT and ROOT not in resolved.parents:
            raise CommandError("提交文件", f"文件路径超出仓库：{raw}")
        if raw == ".git" or raw.startswith(".git/"):
            raise CommandError("提交文件", "不能提交 .git 目录。")
        selected.append(raw)
    return selected


def staged_paths() -> set[str]:
    output = git(
        "-c",
        "core.quotepath=false",
        "diff",
        "--cached",
        "--name-only",
        title="读取暂存区",
    )
    return {line for line in output.splitlines() if line}


def generate() -> str:
    return run(
        [python_executable(), "scripts/generate_site_data.py"],
        "更新资料页面",
    )


def check_content() -> str:
    outputs = [generate()]
    outputs.append(
        run(
            [python_executable(), "scripts/prepublish_check.py"],
            "内容与隐私检查",
        )
    )
    return "\n\n".join(item for item in outputs if item) or "检查完成。"


def build_site() -> str:
    outputs = [check_content()]
    outputs.append(
        run(
            [python_executable(), "-m", "mkdocs", "build", "--strict"],
            "严格编译网站",
            timeout=300,
        )
    )
    return "\n\n".join(item for item in outputs if item) or "编译完成。"


def pull_latest() -> str:
    files = changed_files()
    if files:
        raise CommandError(
            "更新代码",
            "当前有未提交改动。请先提交或手动处理这些文件，再更新远端内容。",
        )
    branch = git("branch", "--show-current", title="检查当前分支")
    if branch != "main":
        raise CommandError("更新代码", f"只能在 main 分支更新，当前为 {branch}。")
    return git("pull", "--ff-only", title="更新代码", timeout=300) or "已经是最新版本。"


def commit_selected(paths: object, message: object) -> str:
    selected = validate_paths(paths)
    text = str(message or "").strip()
    if not text:
        raise CommandError("提交改动", "请填写提交说明。")
    if len(text) > 120:
        raise CommandError("提交改动", "提交说明不能超过 120 个字符。")
    extra_staged = staged_paths() - set(selected)
    if extra_staged:
        formatted = "\n".join(f"- {path}" for path in sorted(extra_staged))
        raise CommandError(
            "提交改动",
            "暂存区中还有未勾选的文件。为避免误提交，请先处理：\n" + formatted,
        )
    git("add", "-A", "--", *selected, title="暂存所选文件")
    return git("commit", "-m", text, title="提交改动", timeout=300)


def push_main() -> str:
    branch = git("branch", "--show-current", title="检查当前分支")
    if branch != "main":
        raise CommandError("推送到 GitHub", f"只能推送 main 分支，当前为 {branch}。")
    return git("push", "origin", "main", title="推送到 GitHub", timeout=300)


class PreviewProcess:
    process: subprocess.Popen[str] | None = None
    log_path = Path(tempfile.gettempdir()) / "wasdar456-mkdocs-preview.log"

    @classmethod
    def running(cls) -> bool:
        return cls.process is not None and cls.process.poll() is None

    @classmethod
    def start(cls) -> str:
        if cls.running():
            return f"本地预览已在 http://{HOST}:{PREVIEW_PORT}/ 运行。"
        log_handle = cls.log_path.open("w", encoding="utf-8")
        cls.process = subprocess.Popen(
            [
                python_executable(),
                "-m",
                "mkdocs",
                "serve",
                "-a",
                f"{HOST}:{PREVIEW_PORT}",
            ],
            cwd=ROOT,
            text=True,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        time.sleep(0.8)
        if cls.process.poll() is not None:
            output = cls.log_path.read_text(encoding="utf-8", errors="replace")
            raise CommandError("启动本地预览", output or "预览进程启动失败。")
        return f"本地预览已启动：http://{HOST}:{PREVIEW_PORT}/"

    @classmethod
    def stop(cls) -> str:
        if not cls.running():
            return "本地预览未运行。"
        assert cls.process is not None
        cls.process.terminate()
        try:
            cls.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.process.kill()
        return "本地预览已停止。"


class PanelServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], token: str):
        super().__init__(address, PanelHandler)
        self.token = token


class PanelHandler(BaseHTTPRequestHandler):
    server_version = "WasdarPanel/1.0"

    def log_message(self, format: str, *args: object) -> None:
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), format % args))

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def send_asset(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route in {"/", "/index.html"}:
            self.send_asset(PANEL_DIR / "index.html", "text/html; charset=utf-8")
        elif route == "/app.js":
            self.send_asset(PANEL_DIR / "app.js", "text/javascript; charset=utf-8")
        elif route == "/styles.css":
            self.send_asset(PANEL_DIR / "styles.css", "text/css; charset=utf-8")
        elif route == "/api/status":
            payload = repository_snapshot()
            payload["token"] = self.server.token  # type: ignore[attr-defined]
            self.send_json(payload)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/action":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        expected = self.server.token  # type: ignore[attr-defined]
        if not secrets.compare_digest(self.headers.get("X-Panel-Token", ""), expected):
            self.send_json({"ok": False, "title": "请求被拒绝", "output": "维护面板令牌无效，请刷新页面。"}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_SIZE:
                raise CommandError("请求无效", "请求内容为空或过大。")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(body, dict):
                raise CommandError("请求无效", "请求格式不正确。")
            action = body.get("action")
            title, output = self.execute_action(action, body)
            self.send_json({"ok": True, "title": title, "output": output})
        except CommandError as exc:
            self.send_json({"ok": False, "title": exc.title, "output": exc.output}, 400)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json({"ok": False, "title": "请求无效", "output": str(exc)}, 400)
        except subprocess.TimeoutExpired:
            self.send_json({"ok": False, "title": "操作超时", "output": "操作运行时间过长，已停止等待。"}, 504)
        except Exception as exc:  # fail closed; details stay on localhost
            self.send_json({"ok": False, "title": "操作失败", "output": str(exc)}, 500)

    @staticmethod
    def execute_action(action: object, body: dict[str, object]) -> tuple[str, str]:
        if action == "pull":
            return "更新完成", pull_latest()
        if action == "check":
            return "检查通过", check_content()
        if action == "build":
            return "编译通过", build_site()
        if action == "preview_start":
            return "预览已启动", PreviewProcess.start()
        if action == "preview_stop":
            return "预览已停止", PreviewProcess.stop()
        if action == "commit":
            return "提交完成", commit_selected(body.get("paths"), body.get("message"))
        if action == "commit_push":
            output = build_site()
            output += "\n\n" + commit_selected(body.get("paths"), body.get("message"))
            output += "\n\n" + push_main()
            return "发布完成", output
        if action == "push":
            return "推送完成", push_main()
        raise CommandError("未知操作", f"不支持的操作：{action}")


def validate_panel_files() -> int:
    required = [PANEL_DIR / "index.html", PANEL_DIR / "styles.css", PANEL_DIR / "app.js"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        print("Missing panel files: " + ", ".join(missing), file=sys.stderr)
        return 1
    snapshot = repository_snapshot()
    print(
        json.dumps(
            {
                "branch": snapshot["branch"],
                "changed_files": len(snapshot["files"]),
                "panel_files": len(required),
            },
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="启动个人主页本地维护面板")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--check", action="store_true", help="只检查面板文件和仓库状态")
    args = parser.parse_args()
    if args.check:
        return validate_panel_files()
    if args.host not in {"127.0.0.1", "localhost"}:
        print("为保证安全，维护面板只能绑定到本机地址。", file=sys.stderr)
        return 2
    token = secrets.token_urlsafe(32)
    server = PanelServer((args.host, args.port), token)
    url = f"http://{args.host}:{args.port}/"
    print(f"Wasdar456 维护面板：{url}")
    print("按 Ctrl+C 关闭。")
    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        PreviewProcess.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
