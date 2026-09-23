#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jev AI 决策服务 - Windows 开机自启管理工具
支持一键将 Jev 桥接服务注册为 Windows 开机静默后台启动（零黑框、零弹窗）。
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
VBS_FILENAME = "RimeJevBridge.vbs"
VBS_PATH = STARTUP_DIR / VBS_FILENAME


def is_autostart_enabled() -> bool:
    """检查是否已设置开机自启动"""
    return VBS_PATH.exists()


def enable_autostart() -> tuple[bool, str]:
    """启用开机自启动（在 Startup 目录下写入静默 VBS 脚本）"""
    try:
        STARTUP_DIR.mkdir(parents=True, exist_ok=True)
        bridge_script = ROOT_DIR / "run_bridge.py"
        
        # 寻找 pythonw.exe（无控制台窗口版本）
        python_exe = Path(sys.executable)
        pythonw_exe = python_exe.with_name("pythonw.exe")
        py_runner = str(pythonw_exe) if pythonw_exe.exists() else str(python_exe)

        vbs_content = f'''Set ws = CreateObject("Wscript.Shell")
ws.CurrentDirectory = "{str(ROOT_DIR)}"
ws.Run """{py_runner}"" ""{str(bridge_script)}""", 0, False
'''
        VBS_PATH.write_text(vbs_content, encoding="gbk")
        return True, "已成功开启开机自启！Jev AI 决策服务将在开机后后台静默运行。"
    except Exception as e:
        return False, f"设置开机自启失败: {e}"


def disable_autostart() -> tuple[bool, str]:
    """取消开机自启动"""
    try:
        if VBS_PATH.exists():
            VBS_PATH.unlink()
        return True, "已成功关闭开机自启。"
    except Exception as e:
        return False, f"取消开机自启失败: {e}"


if __name__ == "__main__":
    if "--enable" in sys.argv:
        ok, msg = enable_autostart()
        print(f"[{'+' if ok else '!'}] {msg}")
    elif "--disable" in sys.argv:
        ok, msg = disable_autostart()
        print(f"[{'+' if ok else '!'}] {msg}")
    elif "--status" in sys.argv:
        st = is_autostart_enabled()
        print(f"Autostart is {'ENABLED' if st else 'DISABLED'}")
    else:
        st = is_autostart_enabled()
        print(f"当前开机自启状态: {'已开启' if st else '未开启'}")
        print("用法: python autostart.py [--enable | --disable | --status]")
