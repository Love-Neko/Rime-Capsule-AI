import os
import sys
import time
import socket
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
from settings_panel.app import SettingsHandler

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

def find_chrome():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None

def find_port(start=19000):
    for port in range(start, start + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    return start

def start_dummy_jev_listener():
    """临时监听 8765 端口使 Jev 状态显示为绿色运行中"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 8765))
        s.listen(1)
        return s
    except Exception:
        return None

def main():
    chrome_bin = find_chrome()
    if not chrome_bin:
        print("[!] Chrome 未找到！")
        return 1

    jev_socket = start_dummy_jev_listener()

    port = find_port()
    server = HTTPServer(("127.0.0.1", port), SettingsHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[*] 临时设置服务运行在 http://127.0.0.1:{port}")

    time.sleep(1)

    url = f"http://127.0.0.1:{port}"
    output_png = ROOT_DIR / "assets" / "preview.png"
    output_png.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--window-size=1200,1680",
        "--virtual-time-budget=3000",
        f"--screenshot={str(output_png)}",
        url
    ]

    print("[*] 正在通过 Chrome Headless 渲染 2x Retina 高清预览图...")
    res = subprocess.run(cmd, capture_output=True, text=False)

    server.shutdown()
    server.server_close()
    if jev_socket:
        jev_socket.close()

    if output_png.exists():
        from PIL import Image
        with Image.open(output_png) as img:
            print(f"[+] 最终图像尺寸: {img.size} ({img.format})")

if __name__ == "__main__":
    main()
