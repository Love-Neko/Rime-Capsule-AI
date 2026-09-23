# Rime AI 智能输入法 (Rime AI Input Method)

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)
![Rime Weasel](https://img.shields.io/badge/Weasel-0.17%2B-orange.svg)
![Design](https://img.shields.io/badge/Style-macOS%20Dark%20Capsule-black.svg)

**融合小狼毫 (Weasel) · 万象拼音海量词库 · TypeSafe Jev AI / Ollama · macOS 极简暗黑胶囊主题 · 图形化交互设置中心**

</div>

---

## ✨ 核心特性

- 🎨 **macOS 极简暗黑胶囊主题（默认内置）**  
  摒弃传统输入法刺眼的亮蓝大色块，采用苹果原装深灰半透明圆角卡片（`#201E1E`）与微亮深灰高亮胶囊（`#423C3C`），文字聚焦纯白，搭配 12pt 苹方粗体（PingFang SC Bold），视觉高级低调。
- 🧠 **双模 AI 语义重排与预测**  
  支持 **TypeSafe Jev AI** 毫秒级上下文决策与本地 **Ollama（如 Qwen 8B）** 开源大模型。支持 **`Tab` 键智能召唤模式**：常规打字零进程、零卡顿、极速飞快；仅在需要长句预测或多音词纠偏时按 Tab 键主动召唤 AI（带 `✦ Jev` 标记）。
- 📚 **万象拼音顶级词库与 400MB 语法模型**  
  集成持续活跃维护的 [amzxyz/rime-wanxiang](https://github.com/amzxyz/rime-wanxiang) 全套 20 个精品词典（45MB 基础大词库 + 地名/诗词/搜狗专业词库，编译后达 82MB 检索表）。支持一键加载官方 **400MB Octagram 语法语言模型**，实现大厂级整句智能预测（带 `∞` 标识）。
- 🎛️ **现代图形化交互设置面板 (Web GUI)**  
  无需面对繁杂晦涩的 YAML 语法！内置基于 Python 原生轻量引擎的 Apple macOS 风格控制中心，支持**实时候选栏动态渲染预览**，一键调节候选词数量、纯英文标点模式、单键 Ctrl 上屏、字体字号并一键编译生效。
- 💎 **高清现代胶囊蓝“中”/灰“A”托盘图标**  
  提供一键注入工具，自动替换任务栏老旧印章图标为高分辨率现代圆角语言图标。
- 🛡️ **严格安全与隐私脱敏**  
  所有敏感凭证（如 Jev API Key）均保存在本地 `.env` 并纳入 `.gitignore`，绝不上传云端，打字数据完全本地闭环。

---

## 📸 效果预览

### 实时候选条效果（macOS 极简暗黑胶囊 + 苹方粗体 + 8 候选）
```text
jian jian de jiu bu zai yi le
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 渐渐地就不在意了 ∞  2. 渐渐地  3. 渐渐的  4. 尖尖的  5. 贱贱的  ... │
└────────────────────────────────────────────────────────────────────────┘
```

### Apple macOS 拟态图形化控制中心 (WebUI)
<div align="center">
  <img src="assets/preview.png" width="780" alt="Rime AI 智能输入法控制中心" style="border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
</div>

---

## 🚀 极速上手

### 1. 克隆或下载本仓库
```bash
git clone https://github.com/Love-Neko/Rime-Capsule-AI.git
cd Rime-Capsule-AI
```

### 2. 双击一键启动懒人包
双击运行仓库根目录下的：
```bat
一键启动.bat
```
后台将自动检测并拉起服务，浏览器将自动弹出 **Rime AI 智能输入法控制中心**。

### 3. 一键个性化定制与部署
在控制面板中，您可以自由勾选与调整：
- **候选词个数**：5 / 7 / 8 / 9 / 10 个（推荐 8 个）
- **单键 Ctrl 极速切换**：开启后，打完英文按 Ctrl 自动将英文字符直接上屏并切回中文；彻底屏蔽 Shift 误触
- **纯英文半角标点模式**：无论中英状态，标点符号（`, . ? ! : ;` 等）永远输出英文半角
- **翻页快捷键**：支持 `[` `]` 翻页、`-` `=` 翻页或 `,` `.` 翻页
- **AI 决策配置**：填入您的 Jev API Key（可选）或配置本地 Ollama 模型
- **400MB 语法模型**：点击【一键下载 400MB 语法模型】享受整句预测体验

调整满意后，点击右下角 **【保存并一键部署到输入法】**，后台将自动生成配置并重新编译加载！

---

## ⌨️ 常用快捷键速查表

| 操作 / 功能 | 快捷键 | 说明 |
| :--- | :--- | :--- |
| **中英模式切换** | `Ctrl` 单键 | 打英文途中直接按 `Ctrl` 将字母上屏并切回中文 |
| **候选词向上翻页** | `[` 或 `-` | 可在设置面板自选按键映射 |
| **候选词向下翻页** | `]` 或 `=` | 可在设置面板自选按键映射 |
| **智能召唤 Jev AI** | `Tab` | 候选框展开时按 Tab 唤醒 Jev AI 决策重排 |
| **大写锁定切换** | 短按 `Caps Lock` | 切换大小写指示灯 |
| **标点符号** | 键盘任意标点键 | 默认或根据设置直接输出半角英文标点 |

---

## 📂 项目结构说明

```text
rime-ai-shurufa/
├── .env.example                  # 环境变量模板（敏感 Key 脱敏）
├── .gitignore                    # 忽略规则（保护隐私密钥与超大二进制模型）
├── LICENSE                       # MIT 开源许可证
├── README.md                     # 本说明文档
├── requirements.txt              # 依赖声明（仅标准库，零强制依赖）
├── 一键启动.bat                   # 🚀 一键启动懒人包（自动拉起服务并弹出设置中心）
├── run_bridge.py                 # Jev AI 桥接服务端入口
│
├── settings_panel/               # 交互设置中心模块
│   ├── app.py                    # 后台 HTTP API 与配置管理
│   ├── settings.json             # 当前保存的自定义配置状态
│   └── web/                      # 前端静态页面
│       ├── index.html            # 控制中心主界面
│       ├── style.css             # Apple macOS Glassmorphism 样式
│       └── script.js             # 实时预览与交互逻辑
│
├── rime_config/                  # 输入法配置核心与字典集
│   ├── dicts/                    # 20 个万象精品拼音词典（45MB+基础词库）
│   ├── opencc/                   # 字符转换规则
│   ├── custom/                   # 方案拓展
│   ├── wanxiang.*.yaml           # 万象拼音方案与词典元数据
│   ├── default.custom.yaml       # 快捷键、切换与候选数配置
│   └── weasel.custom.yaml        # 暗黑胶囊主题与字体定义
│
├── lua/                          # Rime Lua 扩展插件
│   ├── rime.lua                  # Lua 模块加载入口
│   ├── jev_filter.lua            # Jev AI 候选重排过滤器
│   └── wanxiang/                 # 万象核心 Lua 组件集
│
├── tools/                        # 自动化维护工具
│   ├── deploy.py                 # 配置同步与编译部署脚本
│   ├── download_model.py         # 400MB 语法模型断点续传下载工具
│   └── patch_icons.py            # 托盘图标一键更新为 macOS 蓝中/灰A
│
└── assets/                       # 图标与静态资源
    ├── zh_modern.ico             # 高清 macOS 皇家蓝“中”
    └── en_modern.ico             # 高清 macOS 深空灰“A”
```

---

## 🤝 鸣谢与致敬

- [Rime 输入法引擎 (小狼毫 Weasel)](https://github.com/rime/weasel)
- [amzxyz/rime-wanxiang (万象拼音)](https://github.com/amzxyz/rime-wanxiang)
- [TypeSafe AI Jev](https://typesafe.ai)

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源发布。
