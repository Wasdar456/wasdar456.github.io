const state = {
  token: "",
  files: [],
  busy: false,
  previewRunning: false,
  previewUrl: "http://127.0.0.1:8765/",
};

const elements = {
  branch: document.querySelector("#branch"),
  sync: document.querySelector("#sync"),
  latest: document.querySelector("#latest"),
  latestMeta: document.querySelector("#latest-meta"),
  changeCount: document.querySelector("#change-count"),
  fileList: document.querySelector("#file-list"),
  selectAll: document.querySelector("#select-all"),
  commitMessage: document.querySelector("#commit-message"),
  commitButton: document.querySelector("#commit-button"),
  publishButton: document.querySelector("#publish-button"),
  pushButton: document.querySelector("#push-button"),
  aheadMessage: document.querySelector("#ahead-message"),
  workingState: document.querySelector("#working-state"),
  previewButton: document.querySelector("#preview-button"),
  previewCaption: document.querySelector("#preview-caption"),
  logTitle: document.querySelector("#log-title"),
  log: document.querySelector("#log"),
  clearLog: document.querySelector("#clear-log"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function selectedPaths() {
  return [...document.querySelectorAll(".file-checkbox:checked")].map(
    (input) => input.value,
  );
}

function updateSelectionState() {
  const checked = selectedPaths().length;
  const total = state.files.length;
  elements.selectAll.checked = total > 0 && checked === total;
  elements.selectAll.indeterminate = checked > 0 && checked < total;
  elements.commitButton.disabled = state.busy || checked === 0;
  elements.publishButton.disabled = state.busy || checked === 0;
}

function renderFiles() {
  elements.changeCount.textContent = String(state.files.length);
  if (state.files.length === 0) {
    elements.fileList.innerHTML = '<div class="empty-state">工作区干净，没有待提交文件。</div>';
    elements.selectAll.checked = false;
    elements.selectAll.indeterminate = false;
    updateSelectionState();
    return;
  }
  elements.fileList.innerHTML = state.files
    .map(
      (file) => `
        <label class="file-row">
          <input class="file-checkbox" type="checkbox" value="${escapeHtml(file.path)}" />
          <span class="file-kind">${escapeHtml(file.kind)}</span>
          <span class="file-path">${escapeHtml(file.display_path)}</span>
        </label>`,
    )
    .join("");
  document.querySelectorAll(".file-checkbox").forEach((input) => {
    input.addEventListener("change", updateSelectionState);
  });
  updateSelectionState();
}

function renderStatus(data) {
  state.token = data.token;
  state.files = data.files;
  state.previewRunning = data.preview_running;
  state.previewUrl = data.preview_url;
  elements.branch.textContent = data.branch;

  const syncParts = [];
  if (data.ahead) syncParts.push(`领先 ${data.ahead}`);
  if (data.behind) syncParts.push(`落后 ${data.behind}`);
  elements.sync.textContent = syncParts.length ? syncParts.join(" · ") : "已同步";
  elements.latest.textContent = data.latest.subject || "—";
  elements.latestMeta.textContent = `${data.latest.hash || ""}  ${data.latest.date || ""}`;
  elements.aheadMessage.textContent = data.ahead
    ? `有 ${data.ahead} 个本地提交等待推送。`
    : "没有等待推送的本地提交。";
  elements.pushButton.disabled = state.busy || data.ahead === 0;
  elements.previewButton.dataset.action = data.preview_running
    ? "preview_stop"
    : "preview_start";
  elements.previewButton.querySelector("span").textContent = data.preview_running
    ? "停止预览"
    : "本地预览";
  elements.previewCaption.textContent = data.preview_running
    ? "预览正在运行，点击停止"
    : "启动可实时刷新的网站";
  renderFiles();
}

function setBusy(value, label = "") {
  state.busy = value;
  elements.workingState.textContent = value ? label : "";
  document.querySelectorAll("button").forEach((button) => {
    if (button.id !== "clear-log") button.disabled = value;
  });
  if (!value) updateSelectionState();
}

function writeLog(title, output, ok) {
  elements.logTitle.textContent = title;
  elements.log.textContent = output || (ok ? "操作完成。" : "操作失败。请查看终端输出。");
  elements.log.classList.toggle("is-success", ok);
  elements.log.classList.toggle("is-error", !ok);
  elements.log.scrollTop = elements.log.scrollHeight;
}

async function refreshStatus() {
  const response = await fetch("/api/status", { cache: "no-store" });
  if (!response.ok) throw new Error("无法读取仓库状态。");
  renderStatus(await response.json());
}

async function runAction(action, extras = {}) {
  const labels = {
    pull: "正在更新…",
    check: "正在检查…",
    build: "正在编译…",
    preview_start: "正在启动预览…",
    preview_stop: "正在停止预览…",
    commit: "正在提交…",
    commit_push: "正在检查并发布…",
    push: "正在推送…",
  };
  setBusy(true, labels[action] || "正在处理…");
  try {
    const response = await fetch("/api/action", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Panel-Token": state.token,
      },
      body: JSON.stringify({ action, ...extras }),
    });
    const result = await response.json();
    writeLog(result.title, result.output, result.ok);
    if (result.ok && action === "preview_start") {
      window.open(state.previewUrl, "wasdar-preview");
    }
  } catch (error) {
    writeLog("连接失败", error.message, false);
  } finally {
    setBusy(false);
    try {
      await refreshStatus();
    } catch (error) {
      writeLog("状态刷新失败", error.message, false);
    }
  }
}

document.querySelectorAll(".action").forEach((button) => {
  button.addEventListener("click", () => runAction(button.dataset.action));
});

elements.selectAll.addEventListener("change", () => {
  document.querySelectorAll(".file-checkbox").forEach((input) => {
    input.checked = elements.selectAll.checked;
  });
  updateSelectionState();
});

elements.commitButton.addEventListener("click", () => {
  runAction("commit", {
    paths: selectedPaths(),
    message: elements.commitMessage.value,
  });
});

elements.publishButton.addEventListener("click", () => {
  runAction("commit_push", {
    paths: selectedPaths(),
    message: elements.commitMessage.value,
  });
});

elements.pushButton.addEventListener("click", () => runAction("push"));

elements.clearLog.addEventListener("click", () => {
  elements.logTitle.textContent = "操作记录";
  elements.log.textContent = "等待操作。";
  elements.log.classList.remove("is-error", "is-success");
});

refreshStatus().catch((error) => writeLog("初始化失败", error.message, false));
