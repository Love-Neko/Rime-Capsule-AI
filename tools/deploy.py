#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小狼毫配置生成与一键部署引擎
负责将用户设置生成为对应的 YAML 配置并编译应用到系统 Rime 目录中。
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RIME_USER_DIR = Path(os.environ.get("APPDATA", "")) / "Rime"
WEASEL_DIR = Path(r"C:\Program Files\Rime\weasel-0.17.4")


def get_default_config():
    """获取出厂开源默认配置（暗黑胶囊主题，其余标准默认）"""
    return {
        "page_size": 5,
        "ctrl_switch": False,
        "ascii_punct": False,
        "paging_keys": "minus_equal",     # "minus_equal" | "bracket" | "comma_dot"
        "font_face": "PingFang SC Bold, PingFang SC Medium, PingFang SC, Microsoft YaHei UI, Segoe UI",
        "font_point": 12,
        "color_scheme": "mac_minimal_dark",
        "horizontal": True,
        "tab_jev_ai": True,
        "wanxiang_enabled": True
    }


def generate_default_custom_yaml(config):
    """根据配置生成 default.custom.yaml 文本内容"""
    page_size = config.get("page_size", 5)
    ctrl_switch = config.get("ctrl_switch", False)
    ascii_punct = config.get("ascii_punct", False)
    paging_keys = config.get("paging_keys", "minus_equal")
    tab_jev_ai = config.get("tab_jev_ai", True)
    wanxiang = config.get("wanxiang_enabled", True)

    schemas = []
    if wanxiang:
        schemas.append("    - {schema: wanxiang}")
    schemas.append("    - {schema: luna_pinyin_simp}")
    schema_lines = "\n".join(schemas)

    # 快捷键切换
    if ctrl_switch:
        switch_block = f"""  ascii_composer/good_old_caps_lock: true
  ascii_composer/switch_key:
    Caps_Lock: clear
    Shift_L: noop
    Shift_R: noop
    Control_L: commit_code
    Control_R: commit_code"""
    else:
        switch_block = f"""  ascii_composer/good_old_caps_lock: true
  ascii_composer/switch_key:
    Caps_Lock: clear
    Shift_L: inline_ascii
    Shift_R: commit_text
    Control_L: noop
    Control_R: noop"""

    # 标点符号映射
    punct_block = ""
    if ascii_punct:
        symbols = [',', '.', '?', '!', ':', ';', '"', "'", '`', '~', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+', '=', '[', ']', '{', '}', '\\', '|', '/', '<', '>']
        f_lines = [f'    "{s}": "{s}"' for s in symbols]
        h_lines = [f'    "{s}": "{s}"' for s in symbols]
        punct_block = "  punctuator/full_shape:\n" + "\n".join(f_lines) + "\n\n  punctuator/half_shape:\n" + "\n".join(h_lines)

    # 翻页按键绑定
    bindings = []
    if paging_keys == "bracket":
        bindings.append("    - {accept: bracketleft, send: Page_Up, when: has_menu}")
        bindings.append("    - {accept: bracketright, send: Page_Down, when: has_menu}")
    elif paging_keys == "comma_dot":
        bindings.append("    - {accept: comma, send: Page_Up, when: has_menu}")
        bindings.append("    - {accept: period, send: Page_Down, when: has_menu}")
    else:
        bindings.append("    - {accept: minus, send: Page_Up, when: has_menu}")
        bindings.append("    - {accept: equal, send: Page_Down, when: has_menu}")

    if tab_jev_ai:
        bindings.append("    - {accept: Tab, toggle: jev_ai, when: has_menu}")

    bindings_block = "  key_binder/bindings:\n" + "\n".join(bindings)

    content = f"""# default.custom.yaml - 自动生成配置
patch:
  schema_list:
{schema_lines}

  menu/page_size: {page_size}

{switch_block}

{punct_block}

{bindings_block}
"""
    return content


def generate_wanxiang_custom_yaml(config):
    """根据配置生成 wanxiang.custom.yaml"""
    page_size = config.get("page_size", 5)
    ascii_punct = config.get("ascii_punct", False)
    paging_keys = config.get("paging_keys", "minus_equal")
    tab_jev_ai = config.get("tab_jev_ai", True)

    bindings = []
    if paging_keys == "bracket":
        bindings.append("    - {when: has_menu, accept: bracketleft, send: Page_Up}")
        bindings.append("    - {when: has_menu, accept: bracketright, send: Page_Down}")
        bindings.append("    - {when: paging, accept: bracketleft, send: Page_Up}")
        bindings.append("    - {when: paging, accept: bracketright, send: Page_Down}")
    elif paging_keys == "comma_dot":
        bindings.append("    - {when: has_menu, accept: comma, send: Page_Up}")
        bindings.append("    - {when: has_menu, accept: period, send: Page_Down}")
    else:
        bindings.append("    - {when: has_menu, accept: minus, send: Page_Up}")
        bindings.append("    - {when: has_menu, accept: equal, send: Page_Down}")

    if tab_jev_ai:
        bindings.append("    - {when: has_menu, accept: Tab, toggle: jev_ai}")

    bindings_block = "  key_binder/bindings/+:\n" + "\n".join(bindings)

    punct_block = ""
    if ascii_punct:
        symbols = [',', '.', '?', '!', ':', ';', '"', "'", '`', '~', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+', '=', '[', ']', '{', '}', '\\', '|', '/', '<', '>']
        f_lines = [f'    "{s}": "{s}"' for s in symbols]
        h_lines = [f'    "{s}": "{s}"' for s in symbols]
        punct_block = "  punctuator/full_shape:\n" + "\n".join(f_lines) + "\n\n  punctuator/half_shape:\n" + "\n".join(h_lines)

    content = f"""# wanxiang.custom.yaml - 自动生成配置
patch:
  menu/page_size: {page_size}

  engine/filters/@next: lua_filter@jev_filter

{bindings_block}

{punct_block}
"""
    return content


def generate_weasel_custom_yaml(config):
    """根据配置生成 weasel.custom.yaml"""
    font_face = config.get("font_face", "PingFang SC Bold, PingFang SC Medium, PingFang SC, Microsoft YaHei UI, Segoe UI")
    font_point = config.get("font_point", 12)
    horizontal = "true" if config.get("horizontal", True) else "false"
    color_scheme = config.get("color_scheme", "mac_minimal_dark")

    content = f"""# weasel.custom.yaml - 自动生成主题配置
patch:
  "show_notifications": true
  "show_notifications_time": 600
  "style/horizontal": {horizontal}
  "style/inline_preedit": true
  "style/font_face": "{font_face}"
  "style/label_font_face": "PingFang SC Medium, PingFang SC Bold, Segoe UI, Microsoft YaHei UI"
  "style/comment_font_face": "PingFang SC Medium, PingFang SC Bold, Segoe UI, Microsoft YaHei UI"
  "style/font_point": {font_point}
  "style/label_font_point": 10
  "style/comment_font_point": 9.5
  "style/corner_radius": 8
  "style/round_corner": 5
  "style/hilited_corner_radius": 5
  "style/border_width": 0
  "style/color_scheme": {color_scheme}

  "style/layout/align_type": center
  "style/layout/border_width": 0
  "style/layout/margin_x": 10
  "style/layout/margin_y": 6
  "style/layout/spacing": 6
  "style/layout/candidate_spacing": 12
  "style/layout/hilite_spacing": 4
  "style/layout/hilite_padding": 4
  "style/layout/round_corner": 5
  "style/layout/corner_radius": 8
  "style/layout/shadow_radius": 6
  "style/layout/shadow_offset_x": 0
  "style/layout/shadow_offset_y": 2

  "preset_color_schemes/mac_minimal_dark":
    name: "macOS Minimal Dark / 极简深灰胶囊"
    author: "Jev"
    back_color: 0x201E1E
    border_color: 0x302C2C
    shadow_color: 0x60000000
    text_color: 0xE6E0E0
    hilited_text_color: 0xFFFFFF
    hilited_back_color: 0x201E1E
    candidate_text_color: 0xDCD8D8
    label_color: 0x807878
    comment_text_color: 0x807878
    hilited_candidate_back_color: 0x423C3C
    hilited_candidate_text_color: 0xFFFFFF
    hilited_candidate_label_color: 0xD5D0D0
    hilited_comment_text_color: 0xE8BC9B

  "preset_color_schemes/mac_minimal_light":
    name: "macOS Minimal Light / 极简浅色胶囊"
    author: "Jev"
    back_color: 0xF5F5F7
    border_color: 0xE5E5EA
    shadow_color: 0x30000000
    text_color: 0x1D1D1F
    hilited_text_color: 0x000000
    hilited_back_color: 0xF5F5F7
    candidate_text_color: 0x3A3A3C
    label_color: 0x8E8E93
    comment_text_color: 0x8E8E93
    hilited_candidate_back_color: 0xE5E5EA
    hilited_candidate_text_color: 0x000000
    hilited_candidate_label_color: 0x1D1D1F
    hilited_comment_text_color: 0x007AFF
"""
    return content


def sync_and_deploy(config):
    """保存配置并部署同步到系统小狼毫"""
    if not RIME_USER_DIR.exists():
        return False, f"未检测到 Rime 用户目录：{RIME_USER_DIR}"

    # 1. 保存当前配置到 shurufa/rime_config 模板
    rime_cfg = ROOT_DIR / "rime_config"
    (rime_cfg / "default.custom.yaml").write_text(generate_default_custom_yaml(config), encoding="utf-8")
    (rime_cfg / "wanxiang.custom.yaml").write_text(generate_wanxiang_custom_yaml(config), encoding="utf-8")
    (rime_cfg / "weasel.custom.yaml").write_text(generate_weasel_custom_yaml(config), encoding="utf-8")

    # 2. 复制配置与必要文件到 RIME_USER_DIR
    for item in ["default.custom.yaml", "wanxiang.custom.yaml", "weasel.custom.yaml"]:
        src = rime_cfg / item
        if src.exists():
            shutil.copy2(src, RIME_USER_DIR / item)

    # 复制 Lua 脚本
    lua_src = ROOT_DIR / "lua"
    lua_dest = RIME_USER_DIR / "lua"
    if lua_src.exists():
        shutil.copytree(lua_src, lua_dest, dirs_exist_ok=True)
    if (rime_cfg / "rime.lua").exists():
        shutil.copy2(rime_cfg / "rime.lua", RIME_USER_DIR / "rime.lua")

    # 复制词典与 OpenCC（若目标不存在）
    if not (RIME_USER_DIR / "dicts").exists() and (rime_cfg / "dicts").exists():
        shutil.copytree(rime_cfg / "dicts", RIME_USER_DIR / "dicts", dirs_exist_ok=True)
    if not (RIME_USER_DIR / "opencc").exists() and (rime_cfg / "opencc").exists():
        shutil.copytree(rime_cfg / "opencc", RIME_USER_DIR / "opencc", dirs_exist_ok=True)
    if not (RIME_USER_DIR / "wanxiang.schema.yaml").exists():
        for yml in rime_cfg.glob("wanxiang*.yaml"):
            shutil.copy2(yml, RIME_USER_DIR / yml.name)

    # 3. 触发编译部署
    deployer_exe = WEASEL_DIR / "WeaselDeployer.exe"
    if deployer_exe.exists():
        try:
            cmd = f'"{deployer_exe}" /deploy'
            subprocess.run(cmd, shell=True, timeout=60, capture_output=True)
            time.sleep(1)
            # 确保 WeaselServer 启动
            server_exe = WEASEL_DIR / "WeaselServer.exe"
            if server_exe.exists():
                subprocess.Popen([str(server_exe)], creationflags=0x08000000)
            return True, "配置更新并重新编译成功！"
        except Exception as e:
            return False, f"部署编译发生错误：{str(e)}"
    else:
        return True, "配置文件已写入，未找到 WeaselDeployer.exe，请手动重新部署。"


if __name__ == "__main__":
    cfg = get_default_config()
    ok, msg = sync_and_deploy(cfg)
    print(msg)
