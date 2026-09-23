// script.js - Rime AI 设置控制中心前端交互逻辑

let currentConfig = {
  page_size: 8,
  switch_key: "shift_both",
  switch_action: "commit_code",
  ctrl_switch: false,
  ascii_punct: true,
  paging_keys: "bracket",
  font_face: "PingFang SC Bold, PingFang SC Medium, PingFang SC, Microsoft YaHei UI, Segoe UI",
  font_point: 12,
  color_scheme: "mac_minimal_dark",
  custom_colors: {
    back_color: "#1E1E20",
    border_color: "#2C2C30",
    hilited_candidate_back_color: "#3C3C42",
    hilited_candidate_text_color: "#FFFFFF",
    candidate_text_color: "#D8D8DC",
    label_color: "#787880"
  },
  horizontal: true,
  tab_jev_ai: true,
  wanxiang_enabled: true
};

// 预设主题调色盘对照表
const THEME_PALETTES = {
  mac_minimal_dark: {
    back: "#201E1E",
    border: "#302C2C",
    text: "#DCD8D8",
    hilite_back: "#423C3C",
    hilite_text: "#FFFFFF",
    label: "#807878",
    hilite_label: "#D5D0D0",
    comment: "#9BBCE8",
    is_dark: true
  },
  mac_minimal_light: {
    back: "#F5F5F7",
    border: "#E5E5EA",
    text: "#3A3A3C",
    hilite_back: "#E5E5EA",
    hilite_text: "#000000",
    label: "#8E8E93",
    hilite_label: "#1D1D1F",
    comment: "#007AFF",
    is_dark: false
  },
  macos_monterey: {
    back: "#161922",
    border: "#222A38",
    text: "#D0D2D8",
    hilite_back: "#0AA5FF",
    hilite_text: "#FFFFFF",
    label: "#707888",
    hilite_label: "#FFFFFF",
    comment: "#B0E0FF",
    is_dark: true
  },
  catppuccin_mocha: {
    back: "#1E1E2E",
    border: "#313B47",
    text: "#CDD6F4",
    hilite_back: "#45475A",
    hilite_text: "#FFFFFF",
    label: "#6C7C8C",
    hilite_label: "#C6E0F5",
    comment: "#FEB4BE",
    is_dark: true
  },
  tokyo_night: {
    back: "#1A1B26",
    border: "#242C3E",
    text: "#C0D0E0",
    hilite_back: "#283457",
    hilite_text: "#FFFFFF",
    label: "#56687E",
    hilite_label: "#FFD0E0",
    comment: "#7ABADB",
    is_dark: true
  },
  nord_dark: {
    back: "#2E3440",
    border: "#3B434C",
    text: "#D8DFE6",
    hilite_back: "#434C5E",
    hilite_text: "#FFFFFF",
    label: "#617C90",
    hilite_label: "#ECE8E5",
    comment: "#88C0D0",
    is_dark: true
  },
  sakura_pink: {
    back: "#FFF5F8",
    border: "#E5D5E8",
    text: "#4E405C",
    hilite_back: "#E8BEDC",
    hilite_text: "#251530",
    label: "#8C809A",
    hilite_label: "#4E405C",
    comment: "#70408C",
    is_dark: false
  }
};

// 双场景演示候选词数据集
let currentScene = "jev"; // "jev" | "octagram"

const JEV_CANDIDATES = [
  { label: "1.", text: "汽油", comment: "✦ Jev" },
  { label: "2.", text: "骑友", comment: "" },
  { label: "3.", text: "骑游", comment: "" },
  { label: "4.", text: "棋友", comment: "" },
  { label: "5.", text: "期油", comment: "" },
  { label: "6.", text: "岂有", comment: "" },
  { label: "7.", text: "漆油", comment: "" },
  { label: "8.", text: "七有", comment: "" },
  { label: "9.", text: "七游", comment: "" },
  { label: "10.", text: "乞邮", comment: "" }
];

const OCTAGRAM_CANDIDATES = [
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

// 本地自定义词库状态
let phraseEntries = [];
let phraseRawText = "";
let phraseMode = "table"; // "table" | "raw"

let downloadPollTimer = null;

// 初始化生命周期
document.addEventListener("DOMContentLoaded", () => {
  renderPreview();
  loadConfig();
  loadCustomPhrases();
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

  // 加载开机自启状态
  try {
    const autoRes = await fetch("/api/autostart");
    const autoData = await autoRes.json();
    if (autoData && typeof autoData.enabled === "boolean") {
      const sw = document.getElementById("switch-autostart");
      if (sw) sw.checked = autoData.enabled;
    }
  } catch (e) {}
}

// 将配置数据同步到各 UI 控件
function applyConfigToUI(cfg) {
  // 候选词个数
  document.querySelectorAll("#pagesize-control .segment-btn").forEach(btn => {
    btn.classList.toggle("active", parseInt(btn.dataset.value) === parseInt(cfg.page_size));
  });

  // 主题配色
  document.querySelectorAll("#theme-control .theme-card").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.value === cfg.color_scheme);
  });

  // 自定义颜色抽屉显隐与填值
  const customDrawer = document.getElementById("custom-palette-drawer");
  if (customDrawer) {
    customDrawer.style.display = cfg.color_scheme === "custom" ? "block" : "none";
  }
  if (cfg.custom_colors) {
    syncColorPickers(cfg.custom_colors);
  }

  // 字体与字号
  const fontSelect = document.getElementById("font-select");
  if (fontSelect && cfg.font_face) fontSelect.value = cfg.font_face;
  const slider = document.getElementById("fontsize-slider");
  if (slider && cfg.font_point) slider.value = cfg.font_point;
  const badge = document.getElementById("fontsize-val");
  if (badge && cfg.font_point) badge.innerText = cfg.font_point + " pt";

  // 开关与按键类
  document.getElementById("switch-horizontal").checked = cfg.horizontal !== false;
  document.getElementById("switch-punct").checked = !!cfg.ascii_punct;
  document.getElementById("switch-tab-jev").checked = cfg.tab_jev_ai !== false;
  document.getElementById("switch-wanxiang").checked = cfg.wanxiang_enabled !== false;

  // 中英文切换按键与动作
  const switchKeySelect = document.getElementById("switch-key-select");
  if (switchKeySelect) {
    if (cfg.switch_key) {
      switchKeySelect.value = cfg.switch_key;
    } else if (cfg.ctrl_switch) {
      switchKeySelect.value = "ctrl_both";
    } else {
      switchKeySelect.value = "shift_both";
    }
  }

  const switchActionSelect = document.getElementById("switch-action-select");
  if (switchActionSelect && cfg.switch_action) {
    switchActionSelect.value = cfg.switch_action;
  }

  // 翻页按键
  const pagingSelect = document.getElementById("paging-select");
  if (pagingSelect && cfg.paging_keys) pagingSelect.value = cfg.paging_keys;
}

// 同步自定义配色控件与数据
function syncColorPickers(colors) {
  const map = {
    back: ["cp-back", "cp-back-hex", colors.back_color || "#1E1E20"],
    border: ["cp-border", "cp-border-hex", colors.border_color || "#2C2C30"],
    hilite_back: ["cp-hilite-back", "cp-hilite-back-hex", colors.hilited_candidate_back_color || "#3C3C42"],
    hilite_text: ["cp-hilite-text", "cp-hilite-text-hex", colors.hilited_candidate_text_color || "#FFFFFF"],
    cand_text: ["cp-cand-text", "cp-cand-text-hex", colors.candidate_text_color || "#D8D8DC"],
    label: ["cp-label", "cp-label-hex", colors.label_color || "#787880"]
  };

  for (const k in map) {
    const [cId, tId, val] = map[k];
    const cp = document.getElementById(cId);
    const tp = document.getElementById(tId);
    if (cp && val) cp.value = val;
    if (tp && val) tp.value = val;
  }
}

// 获取当前生效的预览调色板
function getActivePalette() {
  if (currentConfig.color_scheme === "custom") {
    const cc = currentConfig.custom_colors || {};
    return {
      back: cc.back_color || "#1E1E20",
      border: cc.border_color || "#2C2C30",
      text: cc.candidate_text_color || "#D8D8DC",
      hilite_back: cc.hilited_candidate_back_color || "#3C3C42",
      hilite_text: cc.hilited_candidate_text_color || "#FFFFFF",
      label: cc.label_color || "#787880",
      hilite_label: cc.hilited_candidate_text_color || "#FFFFFF",
      comment: "#9BBCE8",
      is_dark: true
    };
  }
  return THEME_PALETTES[currentConfig.color_scheme] || THEME_PALETTES.mac_minimal_dark;
}

// 实时候选条渲染
function renderPreview() {
  const bar = document.getElementById("preview-bar");
  const preedit = document.getElementById("preview-preedit");
  if (!bar) return;

  // 1. 更新编码行
  if (preedit) {
    preedit.innerText = currentScene === "jev" ? "汽车qi you" : "jian jian de jiu bu zai yi le";
  }

  // 2. 候选列表截取
  bar.innerHTML = "";
  const count = parseInt(currentConfig.page_size) || 8;
  const rawCands = currentScene === "jev" ? JEV_CANDIDATES : OCTAGRAM_CANDIDATES;
  const cands = rawCands.slice(0, count);

  // 3. 配色渲染
  const palette = getActivePalette();
  bar.style.background = palette.back;
  bar.style.border = "1px solid " + palette.border;

  // 4. 横向/纵向布局
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

    if (idx === 0) {
      item.style.background = palette.hilite_back;
      item.style.color = palette.hilite_text;
    } else {
      item.style.background = "transparent";
      item.style.color = palette.text;
    }

    const labelSpan = document.createElement("span");
    labelSpan.className = "cand-label";
    labelSpan.innerText = cand.label;
    labelSpan.style.color = idx === 0 ? (palette.hilite_label || palette.hilite_text) : palette.label;

    const textSpan = document.createElement("span");
    textSpan.className = "cand-text";
    textSpan.innerText = cand.text;

    item.appendChild(labelSpan);
    item.appendChild(textSpan);

    if (cand.comment) {
      const commentSpan = document.createElement("span");
      commentSpan.className = "cand-comment";
      commentSpan.innerText = cand.comment;
      if (cand.comment.includes("Jev")) {
        commentSpan.style.color = "#5AC8FA";
        commentSpan.style.fontWeight = "600";
      } else {
        commentSpan.style.color = palette.comment || "#9BBCE8";
      }
      item.appendChild(commentSpan);
    }

    bar.appendChild(item);
  });
}

// 加载本地自定义词库
async function loadCustomPhrases() {
  try {
    const res = await fetch("/api/custom_phrase");
    const data = await res.json();
    if (data && data.ok) {
      phraseRawText = data.raw || "";
      phraseEntries = Array.isArray(data.entries) ? data.entries : [];
      renderPhraseTable();
      const rawTextarea = document.getElementById("phrase-raw-textarea");
      if (rawTextarea) rawTextarea.value = phraseRawText;
    }
  } catch (err) {
    console.error("加载自定义词库失败:", err);
  }
}

// 渲染自定义词库表格
function renderPhraseTable(filter = "") {
  const tbody = document.getElementById("phrase-table-body");
  const badge = document.getElementById("phrase-count-badge");
  if (!tbody) return;

  tbody.innerHTML = "";
  const filterLower = (filter || "").trim().toLowerCase();

  const filtered = phraseEntries.filter(item => {
    if (!filterLower) return true;
    return item.text.toLowerCase().includes(filterLower) || item.code.toLowerCase().includes(filterLower);
  });

  if (badge) badge.innerText = `共 ${phraseEntries.length} 条 (当前显示 ${filtered.length} 条)`;

  if (filtered.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="4" style="text-align: center; color: var(--text-muted); padding: 24px;">暂无匹配的自定义词条，请在上方添加新短语</td>`;
    tbody.appendChild(tr);
    return;
  }

  filtered.forEach(entry => {
    // 寻找在原始列表中的真实下标
    const origIndex = phraseEntries.indexOf(entry);
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td class="phrase-text-cell"><strong>${escapeHtml(entry.text)}</strong></td>
      <td><span class="phrase-code-badge">${escapeHtml(entry.code)}</span></td>
      <td class="phrase-weight-cell">${escapeHtml(entry.weight || "5")}</td>
      <td style="text-align: center;">
        <button type="button" class="btn-del-phrase" data-index="${origIndex}" title="删除此词条">🗑️</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // 绑定删除按钮事件
  tbody.querySelectorAll(".btn-del-phrase").forEach(btn => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.index);
      if (!isNaN(idx) && idx >= 0 && idx < phraseEntries.length) {
        phraseEntries.splice(idx, 1);
        renderPhraseTable(document.getElementById("input-phrase-filter")?.value || "");
        showToast("词条已从列表移除（记得点击保存词库）");
      }
    });
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// 事件绑定
function bindEvents() {
  // 双场景演示按钮组
  document.querySelectorAll("#scene-switcher .scene-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#scene-switcher .scene-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentScene = btn.dataset.scene;
      renderPreview();
    });
  });

  // 实测截图查看抽屉切换
  const btnToggleScreenshot = document.getElementById("btn-toggle-screenshot");
  const btnCloseScreenshot = document.getElementById("btn-close-screenshot");
  const viewer = document.getElementById("screenshot-viewer");
  if (btnToggleScreenshot && viewer) {
    btnToggleScreenshot.addEventListener("click", () => {
      viewer.style.display = viewer.style.display === "none" ? "block" : "none";
    });
  }
  if (btnCloseScreenshot && viewer) {
    btnCloseScreenshot.addEventListener("click", () => {
      viewer.style.display = "none";
    });
  }

  // 候选词个数按钮组
  document.querySelectorAll("#pagesize-control .segment-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#pagesize-control .segment-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentConfig.page_size = parseInt(btn.dataset.value);
      renderPreview();
    });
  });

  // 主题预设卡片点击
  document.querySelectorAll("#theme-control .theme-card").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#theme-control .theme-card").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentConfig.color_scheme = btn.dataset.value;

      const customDrawer = document.getElementById("custom-palette-drawer");
      if (customDrawer) {
        customDrawer.style.display = btn.dataset.value === "custom" ? "block" : "none";
      }

      renderPreview();
    });
  });

  // 自定义颜色选择器联动
  bindCustomColorEvents();

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
  // 中英文切换按键与动作监听
  const switchKeySelect = document.getElementById("switch-key-select");
  if (switchKeySelect) {
    switchKeySelect.addEventListener("change", (e) => {
      currentConfig.switch_key = e.target.value;
      currentConfig.ctrl_switch = (e.target.value === "ctrl_both" || e.target.value === "ctrl_l" || e.target.value === "ctrl_r");
    });
  }

  const switchActionSelect = document.getElementById("switch-action-select");
  if (switchActionSelect) {
    switchActionSelect.addEventListener("change", (e) => {
      currentConfig.switch_action = e.target.value;
    });
  }
  document.getElementById("switch-punct").addEventListener("change", (e) => {
    currentConfig.ascii_punct = e.target.checked;
  });
  document.getElementById("switch-tab-jev").addEventListener("change", (e) => {
    currentConfig.tab_jev_ai = e.target.checked;
  });
  const swAuto = document.getElementById("switch-autostart");
  if (swAuto) {
    swAuto.addEventListener("change", async (e) => {
      try {
        const res = await fetch("/api/autostart", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enable: e.target.checked })
        });
        const data = await res.json();
        showToast(data.message || (e.target.checked ? "已开启开机自启" : "已关闭开机自启"));
      } catch (err) {
        showToast("设置开机自启失败: " + err.message);
      }
    });
  }
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

  // 自定义词库事件绑定
  bindCustomPhraseEvents();

  // 保存并一键部署
  document.getElementById("btn-save-deploy").addEventListener("click", handleSaveAndDeploy);

  // 托盘图标一键注入
  document.getElementById("btn-patch-icons").addEventListener("click", handlePatchIcons);

  // 恢复开源出厂默认
  document.getElementById("btn-reset-defaults").addEventListener("click", handleResetDefaults);

  // 400MB 模型下载
  document.getElementById("btn-download-model").addEventListener("click", handleDownloadModel);
}

// 绑定自定义颜色选择器及 Hex 输入框事件
function bindCustomColorEvents() {
  if (!currentConfig.custom_colors) {
    currentConfig.custom_colors = {
      back_color: "#1E1E20",
      border_color: "#2C2C30",
      hilited_candidate_back_color: "#3C3C42",
      hilited_candidate_text_color: "#FFFFFF",
      candidate_text_color: "#D8D8DC",
      label_color: "#787880"
    };
  }

  const pairs = [
    { colorId: "cp-back", textId: "cp-back-hex", key: "back_color" },
    { colorId: "cp-border", textId: "cp-border-hex", key: "border_color" },
    { colorId: "cp-hilite-back", textId: "cp-hilite-back-hex", key: "hilited_candidate_back_color" },
    { colorId: "cp-hilite-text", textId: "cp-hilite-text-hex", key: "hilited_candidate_text_color" },
    { colorId: "cp-cand-text", textId: "cp-cand-text-hex", key: "candidate_text_color" },
    { colorId: "cp-label", textId: "cp-label-hex", key: "label_color" }
  ];

  pairs.forEach(({ colorId, textId, key }) => {
    const cp = document.getElementById(colorId);
    const tp = document.getElementById(textId);
    if (!cp || !tp) return;

    cp.addEventListener("input", (e) => {
      const val = e.target.value.toUpperCase();
      tp.value = val;
      currentConfig.custom_colors[key] = val;
      if (currentConfig.color_scheme === "custom") {
        renderPreview();
      }
    });

    tp.addEventListener("input", (e) => {
      let val = e.target.value.trim().toUpperCase();
      if (!val.startsWith("#") && val.length === 6) val = "#" + val;
      if (/^#[0-9A-F]{6}$/i.test(val)) {
        cp.value = val;
        currentConfig.custom_colors[key] = val;
        if (currentConfig.color_scheme === "custom") {
          renderPreview();
        }
      }
    });
  });
}

// 绑定自定义词库相关事件
function bindCustomPhraseEvents() {
  // 模式切换
  const btnTable = document.getElementById("btn-phrase-mode-table");
  const btnRaw = document.getElementById("btn-phrase-mode-raw");
  const viewTable = document.getElementById("phrase-table-view");
  const viewRaw = document.getElementById("phrase-raw-view");

  if (btnTable && btnRaw) {
    btnTable.addEventListener("click", () => {
      btnTable.classList.add("active");
      btnRaw.classList.remove("active");
      viewTable.style.display = "block";
      viewRaw.style.display = "none";
      phraseMode = "table";
    });

    btnRaw.addEventListener("click", () => {
      btnRaw.classList.add("active");
      btnTable.classList.remove("active");
      viewTable.style.display = "none";
      viewRaw.style.display = "block";
      phraseMode = "raw";
    });
  }

  // 添加词条
  const btnAdd = document.getElementById("btn-add-phrase");
  if (btnAdd) {
    btnAdd.addEventListener("click", () => {
      const textInput = document.getElementById("input-phrase-text");
      const codeInput = document.getElementById("input-phrase-code");
      const weightInput = document.getElementById("input-phrase-weight");

      const text = textInput.value.trim();
      const code = codeInput.value.trim();
      const weight = weightInput.value.trim() || "5";

      if (!text || !code) {
        showToast("请同时输入短语内容和拼音简码！");
        return;
      }

      phraseEntries.unshift({ text, code, weight });
      textInput.value = "";
      codeInput.value = "";
      weightInput.value = "5";

      renderPhraseTable(document.getElementById("input-phrase-filter")?.value || "");
      showToast(`已添加词条「${text}」(${code})，点击保存即可生效！`);
    });
  }

  // 动态宏快速插入
  document.querySelectorAll(".macro-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const text = chip.dataset.text;
      const code = chip.dataset.code;
      const textInput = document.getElementById("input-phrase-text");
      const codeInput = document.getElementById("input-phrase-code");
      if (textInput && text) textInput.value = text;
      if (codeInput && code) codeInput.value = code;
    });
  });

  // 搜索过滤
  const filterInput = document.getElementById("input-phrase-filter");
  if (filterInput) {
    filterInput.addEventListener("input", (e) => {
      renderPhraseTable(e.target.value);
    });
  }

  // 保存词库按钮
  const btnSavePhrase = document.getElementById("btn-save-phrase");
  if (btnSavePhrase) {
    btnSavePhrase.addEventListener("click", handleSaveCustomPhrase);
  }
}

// 单独保存自定义词库
async function handleSaveCustomPhrase() {
  const btn = document.getElementById("btn-save-phrase");
  const origText = btn.innerHTML;
  btn.innerHTML = `<span>⏳ 保存中...</span>`;
  btn.disabled = true;

  try {
    let payload = {};
    if (phraseMode === "raw") {
      const raw = document.getElementById("phrase-raw-textarea").value;
      payload = { raw };
    } else {
      payload = { entries: phraseEntries };
    }

    const res = await fetch("/api/custom_phrase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    showToast(result.message || "自定义词库已保存！");
    loadCustomPhrases();
  } catch (err) {
    showToast("保存词库失败：" + err.message);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}

// 保存并部署
async function handleSaveAndDeploy() {
  const btn = document.getElementById("btn-save-deploy");
  const origText = btn.innerHTML;
  btn.innerHTML = `<span class="btn-icon">⏳</span> 正在部署编译中...`;
  btn.disabled = true;

  try {
    // 1. 如果在编辑词库，顺带提交词库更改
    if (phraseMode === "raw") {
      const raw = document.getElementById("phrase-raw-textarea")?.value;
      if (raw) await fetch("/api/custom_phrase", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw })
      });
    } else if (phraseEntries && phraseEntries.length > 0) {
      await fetch("/api/custom_phrase", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: phraseEntries })
      });
    }

    // 2. 提交配置并触发部署
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
