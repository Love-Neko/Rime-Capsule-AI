#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_dotenv() -> Path:
    base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()
    env_file = base_dir / ".env"
    if not env_file.exists():
        example = Path(__file__).with_name(".env.example")
        if example.exists():
            env_file.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name and name not in os.environ:
                os.environ[name] = value.strip().strip("\"'")
    return env_file


def _first_run_key_prompt(env_file: Path) -> None:
    current_key = os.getenv("TYPESAFE_API_KEY", "").strip()
    if current_key or not sys.stdin or not getattr(sys.stdin, "isatty", lambda: False)():
        return
    print("=" * 56)
    print("  欢迎使用 Jev + Rime 智能输入法桥接服务！")
    print("  首次运行检测到尚未配置 Jev API Key。")
    print("  获取地址: https://console.typesafe.ai/keys")
    print("  Key 将保存在本地 .env 文件中，下次启动不会再提示。")
    print("=" * 56)
    try:
        key = input("请填写你的 Jev Key（直接回车可跳过）: ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not key:
        print("未输入 Key，本次将使用本地规则运行。后续可通过设置面板或编辑 .env 填写。\n")
        return
    lines = env_file.read_text(encoding="utf-8-sig").splitlines() if env_file.exists() else []
    replaced = False
    output = []
    for line in lines:
        if line.lstrip().startswith("TYPESAFE_API_KEY="):
            output.append("TYPESAFE_API_KEY=" + key)
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.append("TYPESAFE_API_KEY=" + key)
    env_file.write_text("\n".join(output) + "\n", encoding="utf-8")
    os.environ["TYPESAFE_API_KEY"] = key
    print("✓ Jev Key 已成功保存到本地 .env，下次启动将自动调用！\n")


_env_file = _load_dotenv()
_first_run_key_prompt(_env_file)

from jev_bridge.config import reload_settings
reload_settings()

from jev_bridge.server import run


if __name__ == "__main__":
    run()
