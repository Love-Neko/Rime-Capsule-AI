#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rime AI 智能输入法交互设置面板 - 后台服务引擎
轻量级、零第三方依赖（纯 Python 标准库），提供配置读写、实时预览、语法模型下载与部署编译 API。
"""

import os
import sys
import json
import time
import socket
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = Path(__file__).resolve().parent / "web"
SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE = ROOT_DIR / ".env.example"

# 动态加载工具模块
sys.path.insert(0, str(ROOT_DIR))
from tools.deploy import get_default_config, sync_and_deploy, RIME_USER_DIR
from tools.download_model import download_grammar_model, get_default_dest, EXPECTED_SIZE
from tools.patch_icons import run_patch
from tools.autostart import is_autostart_enabled, enable_autostart, disable_autostart

def get_custom_phrase_file():
    """获取自定义词库文件路径（优先使用系统 Rime 目录中的，若不存在则使用项目 rime_config）"""
    target = RIME_USER_DIR / "custom_phrase.dict.yaml"
    if target.exists():
        return target
    return ROOT_DIR / "rime_config" / "custom_phrase.dict.yaml"

def parse_custom_phrase(content: str):
    """解析 custom_phrase.dict.yaml 内容，提取词条列表"""
    entries = []
    lines = content.splitlines()
    in_entries = False
    for line in lines:
        stripped = line.strip()
        if not in_entries:
            if stripped == "...":
                in_entries = True
            continue
        if not stripped or stripped.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            text = parts[0].strip()
            code = parts[1].strip()
            weight = parts[2].strip() if len(parts) >= 3 else "5"
            entries.append({"text": text, "code": code, "weight": weight})
    return entries

def build_custom_phrase_yaml(entries: list) -> str:
    """由词条列表重新构建带有完整万象动态宏注释的 custom_phrase.dict.yaml"""
    header = """# Rime dictionary
# encoding: utf-8
# 
# 为应对9键、14键、18键等场景下使用用户词
# 用户词库变更为bin引用，而不是userdb-table

# 【万象候选动态格式化说明】
# --------------------------------------------------
# 1. 时间占位 ( \\ + 字母 )
# \\T:时辰(午时)  \\K:刻(三刻)
# \\Y:年(2025)    \\y:年(25)     \\m:月(01)    \\N:月(1)
# \\d:日(09)      \\j:日(9)      \\H:时(08)    \\G:时(8)
# \\I:时(12h)     \\l:时(12h不带零)
# \\C:中文星期全称(星期一)  \\D:中文星期简称(周一)
# \\E:英文星期全称(Monday)  \\F:英文星期简称(Mon)
# \\w:ISO周数(10)
# \\M:分(05)      \\S:秒(09)     \\p:am/pm     \\P:AM/PM
# \\O:时区(+08:00) \\o:时区(+0800) \\A:凌晨/上午/中午/下午/晚上
# --------------------------------------------------
# 2. 数量重复 ( 字符 + \\ + 数字 )
# a\\3 => aaa     哈\\2 => 哈哈     !\\10 => !!!!!
# --------------------------------------------------
# 3. 基础转义
# \\n : 换行符    \\s : 空格    \\t : 制表符
# [[...]] : 区块内不转义 (如: [[\\Y]] 输出 \\Y)
# --------------------------------------------------
# 示例: 编码 csck -> 此时此刻：\\T\\K  =>  此时此刻：午时三刻
# 示例: 编码 rq -> \\Y-\\m-\\d \\D  =>  2025-03-12 周三
---
name: custom_phrase
version: "LTS"
sort: by_weight
use_preset_vocabulary: false
...
"""
    body_lines = []
    for item in entries:
        t = str(item.get("text", "")).strip()
        c = str(item.get("code", "")).strip()
        w = str(item.get("weight", "5")).strip()
        if t and c:
            body_lines.append(f"{t}\t{c}\t{w}")
    return header + "\n".join(body_lines) + "\n"


# 全局模型下载状态追踪
download_state = {
    "is_downloading": False,
    "percent": 0.0,
    "current_bytes": 0,
    "total_bytes": EXPECTED_SIZE,
    "message": "未开始",
    "speed": "0 KB/s",
    "last_time": 0,
    "last_bytes": 0,
    "error": None
}


def load_env():
    """读取本地 .env 文件中的键值"""
    env_vars = {}
    target_file = ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE
    if target_file.exists():
        for line in target_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("'").strip('"')
    return env_vars


def save_env(vars_to_update):
    """保存环境变量到本地 .env（不追踪到 git）"""
    lines = []
    existing = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                k, v = line_str.split("=", 1)
                existing[k.strip()] = v.strip()
                if k.strip() in vars_to_update:
                    lines.append(f"{k.strip()}={vars_to_update[k.strip()]}")
                    continue
            lines.append(line)
    else:
        if ENV_EXAMPLE.exists():
            lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                k, v = line_str.split("=", 1)
                if k.strip() in vars_to_update:
                    lines[i] = f"{k.strip()}={vars_to_update[k.strip()]}"
                    existing[k.strip()] = True

    for k, v in vars_to_update.items():
        if k not in existing:
            lines.append(f"{k}={v}")

    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


def load_settings():
    """加载配置"""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return get_default_config()


def save_settings(cfg):
    """保存配置"""
    SETTINGS_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


class SettingsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format, *args):
        # 静默常规静态资源请求日志，保持控制台整洁
        pass

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/assets/"):
            rel_path = path.lstrip("/").replace("/", os.sep)
            file_path = ROOT_DIR / rel_path
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                mime = "image/png" if file_path.suffix.lower() == ".png" else "image/x-icon" if file_path.suffix.lower() == ".ico" else "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "File Not Found")
                return

        if path == "/api/config":
            cfg = load_settings()
            env_vars = load_env()
            # 融合敏感字段到 API（仅用于本地交互，密码遮罩）
            res = {
                "config": cfg,
                "env": {
                    "has_key": bool(env_vars.get("TYPESAFE_API_KEY") and env_vars.get("TYPESAFE_API_KEY") != "your_typesafe_api_key_here"),
                    "masked_key": (env_vars.get("TYPESAFE_API_KEY", "")[:6] + "..." + env_vars.get("TYPESAFE_API_KEY", "")[-4:]) if env_vars.get("TYPESAFE_API_KEY") and env_vars.get("TYPESAFE_API_KEY") != "your_typesafe_api_key_here" else "",
                    "local_ollama": env_vars.get("LOCAL_OLLAMA_ENABLED", "0") == "1",
                    "ollama_url": env_vars.get("LOCAL_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                    "ollama_model": env_vars.get("LOCAL_OLLAMA_MODEL", "qwen3:8b")
                }
            }
            self.send_json(res)
            return

        elif path == "/api/status":
            # 检查语法模型
            model_dest = get_default_dest()
            model_installed = model_dest.exists() and model_dest.stat().st_size >= EXPECTED_SIZE - 2048
            model_size_mb = (model_dest.stat().st_size / (1024*1024)) if model_dest.exists() else 0

            # 检查小狼毫进程
            weasel_running = False
            try:
                out = os.popen('tasklist /FI "IMAGENAME eq WeaselServer.exe" /NH').read()
                weasel_running = "WeaselServer.exe" in out
            except Exception:
                pass

            # 检查 Jev AI 端口 8765
            jev_running = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                if s.connect_ex(("127.0.0.1", 8765)) == 0:
                    jev_running = True
                s.close()
            except Exception:
                pass

            self.send_json({
                "model_installed": model_installed,
                "model_size_mb": round(model_size_mb, 1),
                "weasel_running": weasel_running,
                "jev_running": jev_running
            })
            return

        elif path == "/api/model/progress":
            self.send_json(download_state)
            return

        elif path == "/api/autostart":
            self.send_json({"ok": True, "enabled": is_autostart_enabled()})
            return

        elif path == "/api/custom_phrase":
            try:
                target_file = get_custom_phrase_file()
                content = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
                entries = parse_custom_phrase(content)
                self.send_json({"ok": True, "raw": content, "entries": entries})
            except Exception as e:
                self.send_json({"ok": False, "message": str(e), "entries": []}, code=500)
            return

        # 默认静态页面
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length) if length > 0 else b"{}"

        try:
            payload = json.loads(post_data.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/config":
            cfg = payload.get("config", {})
            save_settings(cfg)

            # 更新 .env
            env_updates = {}
            api_key = payload.get("api_key")
            if api_key and api_key != "PRESERVED":
                env_updates["TYPESAFE_API_KEY"] = api_key.strip()
            if "local_ollama" in payload:
                env_updates["LOCAL_OLLAMA_ENABLED"] = "1" if payload["local_ollama"] else "0"
            if "ollama_url" in payload:
                env_updates["LOCAL_OLLAMA_BASE_URL"] = payload["ollama_url"].strip()
            if "ollama_model" in payload:
                env_updates["LOCAL_OLLAMA_MODEL"] = payload["ollama_model"].strip()
            if env_updates:
                save_env(env_updates)

            self.send_json({"ok": True, "message": "配置已成功保存！"})
            return

        elif path == "/api/deploy":
            # 保存并部署
            cfg = payload.get("config", load_settings())
            save_settings(cfg)
            ok, msg = sync_and_deploy(cfg)
            self.send_json({"ok": ok, "message": msg})
            return

        elif path == "/api/model/download":
            if download_state["is_downloading"]:
                self.send_json({"ok": False, "message": "模型已经在下载中..."})
                return

            def bg_download():
                download_state["is_downloading"] = True
                download_state["error"] = None
                download_state["percent"] = 0.0
                download_state["message"] = "连接下载节点中..."
                download_state["last_time"] = time.time()
                download_state["last_bytes"] = 0

                def on_progress(pct, cur, total, msg):
                    download_state["percent"] = round(pct, 1)
                    download_state["current_bytes"] = cur
                    download_state["total_bytes"] = total
                    download_state["message"] = msg
                    now = time.time()
                    dt = now - download_state["last_time"]
                    if dt > 1.0:
                        db = cur - download_state["last_bytes"]
                        speed_kbs = (db / dt) / 1024
                        if speed_kbs >= 1024:
                            download_state["speed"] = f"{speed_kbs/1024:.2f} MB/s"
                        else:
                            download_state["speed"] = f"{speed_kbs:.1f} KB/s"
                        download_state["last_time"] = now
                        download_state["last_bytes"] = cur

                ok, msg = download_grammar_model(progress_callback=on_progress)
                download_state["is_downloading"] = False
                download_state["message"] = msg
                if not ok:
                    download_state["error"] = msg

            threading.Thread(target=bg_download, daemon=True).start()
            self.send_json({"ok": True, "message": "已在后台启动模型下载！"})
            return

        elif path == "/api/patch_icons":
            ok, res = run_patch()
            self.send_json({"ok": ok, "details": res, "message": "托盘图标注入完成！请重启 Explorer 或注销重登查看。" if ok else "部分图标更新失败"})
            return

        elif path == "/api/reset_default":
            cfg = get_default_config()
            save_settings(cfg)
            self.send_json({"ok": True, "config": cfg, "message": "已恢复开源出厂默认配置！"})
            return

        elif path == "/api/autostart":
            enable = bool(payload.get("enable", False))
            ok, msg = enable_autostart() if enable else disable_autostart()
            self.send_json({"ok": ok, "message": msg, "enabled": is_autostart_enabled()})
            return

        elif path == "/api/custom_phrase":
            try:
                raw_content = payload.get("raw")
                if raw_content is None and "entries" in payload:
                    raw_content = build_custom_phrase_yaml(payload["entries"])
                if raw_content is not None:
                    # 保存到项目 rime_config
                    cfg_path = ROOT_DIR / "rime_config" / "custom_phrase.dict.yaml"
                    cfg_path.parent.mkdir(parents=True, exist_ok=True)
                    cfg_path.write_text(raw_content, encoding="utf-8")

                    # 同步到系统 Rime 目录
                    if RIME_USER_DIR.exists():
                        (RIME_USER_DIR / "custom_phrase.dict.yaml").write_text(raw_content, encoding="utf-8")

                    self.send_json({"ok": True, "message": "自定义词库已成功保存！点击【保存并一键部署】或重新部署后生效。"})
                else:
                    self.send_json({"ok": False, "message": "无效的数据内容"}, code=400)
            except Exception as e:
                self.send_json({"ok": False, "message": f"保存词库失败：{str(e)}"}, code=500)
            return

        self.send_json({"ok": False, "message": "未知 API"}, code=404)


def find_free_port(start_port=18888):
    for port in range(start_port, start_port + 50):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    return start_port


def run_server(open_browser=True):
    port = find_free_port()
    server = HTTPServer(("127.0.0.1", port), SettingsHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"\n========================================================")
    print(f"  Rime AI 智能输入法交互设置中心已启动！")
    print(f"  控制面板地址: {url}")
    print(f"  按 Ctrl+C 可停止设置服务。")
    print(f"========================================================\n")

    if open_browser:
        threading.Thread(target=lambda: (time.sleep(0.5), webbrowser.open(url)), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n设置面板已安全退出。")
        server.server_close()


if __name__ == "__main__":
    run_server(open_browser=True)
