// script.js - Rime AI 设置控制中心前端交互逻辑

let currentConfig = {
  page_size: 8,
  ctrl_switch: true,
  ascii_punct: true,
  paging_keys: "bracket",
  font_face: "PingFang SC Bold, PingFang SC Medium, PingFang SC, Microsoft YaHei UI, Segoe UI",
  font_point: 12,
  color_scheme: "mac_minimal_dark",
  horizontal: true,
  tab_jev_ai: true,
  wanxiang_enabled: true
};

const SAMPLE_CANDIDATES = [
  { label: "1.", text: "渐渐地就不在意了", comment: "∞" },
  { label: "2.", text: "渐渐地", comment: "" },
  { label: "3.", text: "渐渐的", comment: "" },
  { label: "4.", text: "尖尖的", comment: "" },
  { label: "5.", text: "贱贱的", comment: "" },
  { label: "6.", text: "贱贱哒", comment: "" },
  { label: "7.", text: "渐渐", comment: "" },
  { label: "8.", text: "件件", comment: "" },
  { label: "9.", text: "蹇蹇", comment: "" },
  { label: "10.", text: "简简", comment: "" }
];

let downloadPollTimer = null;

// 初始化
document.addEventListener("DOMContentLoaded", () => {
  loadConfig();
  fetchSystemStatus();
  setInterval(fetchSystemStatus, 4000);
  bindEvents();
});

// 加载后台配置
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();
    if (data && data.config) {
      currentConfig = Object.assign(currentConfig, data.config);
      applyConfigToUI(currentConfig);
      renderPreview();
    }
    if (data && data.env) {
      if (data.env.has_key) {
        document.getElementById("input-api-key").placeholder = "已配置 Key: " + data.env.masked_key;
        document.getElementById("input-api-key").dataset.configured = "true";
      }
      document.getElementById("switch-ollama").checked = data.env.local_ollama;
      document.getElementById("ollama-options").style.display = data.env.local_ollama ? "block" : "none";
      if (data.env.ollama_url) document.getElementById("input-ollama-url").value = data.env.ollama_url;
      if (data.env.ollama_model) document.getElementById("input-ollama-model").value = data.env.ollama_model;
    }
  } catch (err) {
    console.error("加载配置失败:", err);
  }
}

// 将配置数据同步到各 UI 控件
function applyConfigToUI(cfg) {
  // 候选词个数
  document.querySelectorAll("#pagesize-control .segment-btn").forEach(btn => {
    btn.classList.toggle("active", parseInt(btn.dataset.value) === parseInt(cfg.page_size));
  });

  // 主题
  document.querySelectorAll("#theme-control .segment-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.value === cfg.color_scheme);
  });

  // 字体与字号
  const fontSelect = document.getElementById("font-select");
  if (fontSelect) fontSelect.value = cfg.font_face;
  const slider = document.getElementById("fontsize-slider");
  if (slider) slider.value = cfg.font_point;
  const badge = document.getElementById("fontsize-val");
  if (badge) badge.innerText = cfg.font_point + " pt";

  // 开关类
  document.getElementById("switch-horizontal").checked = cfg.horizontal !== false;
  document.getElementById("switch-ctrl").checked = !!cfg.ctrl_switch;
  document.getElementById("switch-punct").checked = !!cfg.ascii_punct;
  document.getElementById("switch-tab-jev").checked = cfg.tab_jev_ai !== false;
  document.getElementById("switch-wanxiang").checked = cfg.wanxiang_enabled !== false;

  // 翻页按键
  const pagingSelect = document.getElementById("paging-select");
  if (pagingSelect && cfg.paging_keys) pagingSelect.value = cfg.paging_keys;
}

// 实时候选条渲染
function renderPreview() {
  const bar = document.getElementById("preview-bar");
  if (!bar) return;

  bar.innerHTML = "";
  const count = parseInt(currentConfig.page_size) || 8;
  const cands = SAMPLE_CANDIDATES.slice(0, count);

  // 主题样式切换
  const isLight = currentConfig.color_scheme === "mac_minimal_light";
  if (isLight) {
    bar.style.background = "#F5F5F7";
    bar.style.border = "1px solid #E5E5EA";
  } else {
    bar.style.background = "#201E1E";
    bar.style.border = "1px solid #302C2C";
  }

  // 横向/纵向
  if (currentConfig.horizontal === false) {
    bar.style.flexDirection = "column";
    bar.style.alignItems = "flex-start";
  } else {
    bar.style.flexDirection = "row";
    bar.style.alignItems = "center";
  }

  cands.forEach((cand, idx) => {
    const item = document.createElement("div");
    item.className = "candidate-item" + (idx === 0 ? " hilited" : "");
    item.style.fontSize = (currentConfig.font_point || 12) + "pt";
    item.style.fontFamily = currentConfig.font_face || "inherit";

    if (isLight) {
      if (idx === 0) {
        item.style.background = "#E5E5EA";
        item.style.color = "#000000";
      } else {
        item.style.background = "transparent";
        item.style.color = "#3A3A3C";
      }
    } else {
      if (idx === 0) {
        item.style.background = "#423C3C";
        item.style.color = "#FFFFFF";
      } else {
        item.style.background = "transparent";
        item.style.color = "#DCD8D8";
      }
    }

    const labelSpan = document.createElement("span");
    labelSpan.className = "cand-label";
    labelSpan.innerText = cand.label;
    if (isLight) {
      labelSpan.style.color = idx === 0 ? "#1D1D1F" : "#8E8E93";
    }

    const textSpan = document.createElement("span");
    textSpan.className = "cand-text";
    textSpan.innerText = cand.text;

    item.appendChild(labelSpan);
    item.appendChild(textSpan);

    if (cand.comment) {
      const commentSpan = document.createElement("span");
      commentSpan.className = "cand-comment";
      commentSpan.innerText = cand.comment;
      if (isLight) commentSpan.style.color = "#007AFF";
      item.appendChild(commentSpan);
    }

    bar.appendChild(item);
  });
}

// 事件绑定
function bindEvents() {
  // 候选词个数按钮组
  document.querySelectorAll("#pagesize-control .segment-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#pagesize-control .segment-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentConfig.page_size = parseInt(btn.dataset.value);
      renderPreview();
    });
  });

  // 主题切换
  document.querySelectorAll("#theme-control .segment-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#theme-control .segment-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentConfig.color_scheme = btn.dataset.value;
      renderPreview();
    });
  });

  // 字体选择
  document.getElementById("font-select").addEventListener("change", (e) => {
    currentConfig.font_face = e.target.value;
    renderPreview();
  });

  // 字号滑块
  const slider = document.getElementById("fontsize-slider");
  slider.addEventListener("input", (e) => {
    currentConfig.font_point = parseFloat(e.target.value);
    document.getElementById("fontsize-val").innerText = e.target.value + " pt";
    renderPreview();
  });

  // 开关切换
  document.getElementById("switch-horizontal").addEventListener("change", (e) => {
    currentConfig.horizontal = e.target.checked;
    renderPreview();
  });
  document.getElementById("switch-ctrl").addEventListener("change", (e) => {
    currentConfig.ctrl_switch = e.target.checked;
  });
  document.getElementById("switch-punct").addEventListener("change", (e) => {
    currentConfig.ascii_punct = e.target.checked;
  });
  document.getElementById("switch-tab-jev").addEventListener("change", (e) => {
    currentConfig.tab_jev_ai = e.target.checked;
  });
  document.getElementById("switch-wanxiang").addEventListener("change", (e) => {
    currentConfig.wanxiang_enabled = e.target.checked;
  });
  document.getElementById("paging-select").addEventListener("change", (e) => {
    currentConfig.paging_keys = e.target.value;
  });

  // Ollama 展开折叠
  document.getElementById("switch-ollama").addEventListener("change", (e) => {
    document.getElementById("ollama-options").style.display = e.target.checked ? "block" : "none";
  });

  // 密码眼睛切换
  const eyeBtn = document.getElementById("btn-toggle-key-eye");
  const keyInput = document.getElementById("input-api-key");
  eyeBtn.addEventListener("click", () => {
    if (keyInput.type === "password") {
      keyInput.type = "text";
      eyeBtn.innerText = "🔒";
    } else {
      keyInput.type = "password";
      eyeBtn.innerText = "👁";
    }
  });

  // 保存并一键部署
  document.getElementById("btn-save-deploy").addEventListener("click", handleSaveAndDeploy);

  // 托盘图标一键注入
  document.getElementById("btn-patch-icons").addEventListener("click", handlePatchIcons);

  // 恢复开源出厂默认
  document.getElementById("btn-reset-defaults").addEventListener("click", handleResetDefaults);

  // 400MB 模型下载
  document.getElementById("btn-download-model").addEventListener("click", handleDownloadModel);
}

// 保存并部署
async function handleSaveAndDeploy() {
  const btn = document.getElementById("btn-save-deploy");
  const origText = btn.innerHTML;
  btn.innerHTML = `<span class="btn-icon">⏳</span> 正在部署编译中...`;
  btn.disabled = true;

  try {
    const rawKey = document.getElementById("input-api-key").value.trim();
    const payload = {
      config: currentConfig,
      api_key: rawKey ? rawKey : "PRESERVED",
      local_ollama: document.getElementById("switch-ollama").checked,
      ollama_url: document.getElementById("input-ollama-url").value.trim(),
      ollama_model: document.getElementById("input-ollama-model").value.trim()
    };

    const res = await fetch("/api/deploy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    showToast(result.message || "部署成功！");
    fetchSystemStatus();
  } catch (err) {
    showToast("部署请求失败：" + err.message);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}

// 注入托盘图标
async function handlePatchIcons() {
  const btn = document.getElementById("btn-patch-icons");
  btn.disabled = true;
  showToast("正在为小狼毫注入 macOS 胶囊蓝中/灰A 图标...");
  try {
    const res = await fetch("/api/patch_icons", { method: "POST" });
    const result = await res.json();
    showToast(result.message || "图标已注入！");
  } catch (err) {
    showToast("图标注入失败：" + err.message);
  } finally {
    btn.disabled = false;
  }
}

// 恢复出厂默认
async function handleResetDefaults() {
  if (!confirm("确定要恢复开源出厂默认配置吗？（将保留暗黑胶囊主题，其余恢复为标准 5 候选等）")) return;

  try {
    const res = await fetch("/api/reset_default", { method: "POST" });
    const result = await res.json();
    if (result && result.config) {
      currentConfig = result.config;
      applyConfigToUI(currentConfig);
      renderPreview();
      showToast("已恢复出厂配置，可点击【保存并一键部署】生效。");
    }
  } catch (err) {
    showToast("恢复默认失败：" + err.message);
  }
}

// 400MB 语法模型下载
async function handleDownloadModel() {
  const btn = document.getElementById("btn-download-model");
  btn.disabled = true;
  document.getElementById("download-progress-container").style.display = "flex";

  try {
    const res = await fetch("/api/model/download", { method: "POST" });
    const data = await res.json();
    showToast(data.message || "下载任务已提交");
    startPollDownload();
  } catch (err) {
    showToast("提交下载失败：" + err.message);
    btn.disabled = false;
  }
}

function startPollDownload() {
  if (downloadPollTimer) clearInterval(downloadPollTimer);
  downloadPollTimer = setInterval(async () => {
    try {
      const res = await fetch("/api/model/progress");
      const st = await res.json();

      document.getElementById("progress-bar-fill").style.width = st.percent + "%";
      document.getElementById("progress-pct-text").innerText = st.percent + "%";
      document.getElementById("progress-speed-text").innerText = st.speed || "";
      document.getElementById("progress-status-text").innerText = st.message || "";

      if (!st.is_downloading) {
        clearInterval(downloadPollTimer);
        document.getElementById("btn-download-model").disabled = false;
        fetchSystemStatus();
        if (st.error) {
          showToast("模型下载未完成：" + st.error);
        } else {
          showToast("400MB 语法模型下载完成！");
        }
      }
    } catch (e) {}
  }, 1000);
}

// 系统状态轮询
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/status");
    const st = await res.json();

    // Weasel
    const pWeasel = document.getElementById("pill-weasel");
    pWeasel.className = "status-pill " + (st.weasel_running ? "online" : "offline");
    pWeasel.querySelector(".label").innerText = "小狼毫: " + (st.weasel_running ? "运行中" : "未启动");

    // Model
    const pModel = document.getElementById("pill-model");
    const badge = document.getElementById("model-status-badge");
    if (st.model_installed) {
      pModel.className = "status-pill online";
      pModel.querySelector(".label").innerText = `400MB 模型: 已就绪 (${st.model_size_mb} MB)`;
      badge.className = "status-badge ready";
      badge.innerText = `已就绪 (${st.model_size_mb} MB)`;
      document.getElementById("btn-download-text").innerText = "模型已就绪 (可点击重新下载)";
    } else {
      pModel.className = "status-pill offline";
      pModel.querySelector(".label").innerText = "400MB 模型: 未安装";
      badge.className = "status-badge missing";
      badge.innerText = "未安装 (建议下载)";
      document.getElementById("btn-download-text").innerText = "一键下载 400MB 语法模型";
    }

    // Jev
    const pJev = document.getElementById("pill-jev");
    pJev.className = "status-pill " + (st.jev_running ? "online" : "offline");
    pJev.querySelector(".label").innerText = "Jev AI 桥接: " + (st.jev_running ? "运行中" : "未运行");
  } catch (err) {}
}

// 弹出 Toast 提示
function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.innerText = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}
