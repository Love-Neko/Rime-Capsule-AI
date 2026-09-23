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
    """获取出厂开源默认配置（暗黑胶囊主题，8个候选词，其余标准默认）"""
    return {
        "page_size": 8,
        "switch_key": "shift_both",       # "shift_both" | "shift_l" | "shift_r" | "ctrl_both" | "ctrl_l" | "ctrl_r" | "none"
        "switch_action": "commit_code",   # "commit_code" | "clear" | "inline_ascii" | "commit_text"
        "ctrl_switch": False,             # 保留向后兼容
        "ascii_punct": False,
        "paging_keys": "minus_equal",     # "minus_equal" | "bracket" | "comma_dot"
        "font_face": "PingFang SC Bold, PingFang SC Medium, PingFang SC, Microsoft YaHei UI, Segoe UI",
        "font_point": 12,
        "color_scheme": "mac_minimal_dark",
        "custom_colors": {
            "back_color": "#1E1E20",
            "border_color": "#2C2C30",
            "hilited_candidate_back_color": "#3C3C42",
            "hilited_candidate_text_color": "#FFFFFF",
            "candidate_text_color": "#D8D8DC",
            "label_color": "#787880"
        },
        "horizontal": True,
        "tab_jev_ai": True,
        "wanxiang_enabled": True
    }


def generate_default_custom_yaml(config):
    """根据配置生成 default.custom.yaml 文本内容"""
    page_size = config.get("page_size", 5)
    ascii_punct = config.get("ascii_punct", False)
    paging_keys = config.get("paging_keys", "minus_equal")
    tab_jev_ai = config.get("tab_jev_ai", True)
    wanxiang = config.get("wanxiang_enabled", True)

    schemas = []
    if wanxiang:
        schemas.append("    - {schema: wanxiang}")
    schemas.append("    - {schema: luna_pinyin_simp}")
    schema_lines = "\n".join(schemas)

    # 中英文切换按键自定义配置
    switch_key = config.get("switch_key")
    if not switch_key:
        if config.get("ctrl_switch", False):
            switch_key = "ctrl_both"
        else:
            switch_key = "shift_both"

    action = config.get("switch_action", "commit_code")

    k_shift_l = "noop"
    k_shift_r = "noop"
    k_ctrl_l = "noop"
    k_ctrl_r = "noop"

    if switch_key == "shift_both":
        k_shift_l = action
        k_shift_r = action
    elif switch_key == "shift_l":
        k_shift_l = action
    elif switch_key == "shift_r":
        k_shift_r = action
    elif switch_key == "ctrl_both":
        k_ctrl_l = action
        k_ctrl_r = action
    elif switch_key == "ctrl_l":
        k_ctrl_l = action
    elif switch_key == "ctrl_r":
        k_ctrl_r = action
    elif switch_key == "none":
        pass

    switch_block = f"""  ascii_composer/good_old_caps_lock: true
  ascii_composer/switch_key:
    Caps_Lock: clear
    Shift_L: {k_shift_l}
    Shift_R: {k_shift_r}
    Control_L: {k_ctrl_l}
    Control_R: {k_ctrl_r}"""

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
    page_size = config.get("page_size", 8)
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

    bindings_block = "  key_binder/import_preset: default\n  key_binder/bindings:\n" + "\n".join(bindings)

    punct_block = ""
    if ascii_punct:
        symbols = [',', '.', '?', '!', ':', ';', '"', "'", '`', '~', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+', '=', '[', ']', '{', '}', '\\', '|', '/', '<', '>']
        f_lines = [f'    "{s}": "{s}"' for s in symbols]
        h_lines = [f'    "{s}": "{s}"' for s in symbols]
        punct_block = "  punctuator/full_shape:\n" + "\n".join(f_lines) + "\n\n  punctuator/half_shape:\n" + "\n".join(h_lines)

    content = f"""# wanxiang.custom.yaml - 自动生成配置
patch:
  menu/page_size: {page_size}

  # 注册 jev_ai 开关
  switches/@next:
    name: jev_ai
    reset: 0
    states: [AI关, AI开]

  # 挂载 Jev AI 语义重排过滤器
  engine/filters/@next: lua_filter@jev_filter

{bindings_block}

{punct_block}
"""
    return content


def hex_to_weasel_color(hex_str: str, default: str = "0x201E1E") -> str:
    """将 CSS Hex 颜色 (#RRGGBB) 转换为小狼毫原生 BGR 格式 (0xBBGGRR)"""
    if not hex_str:
        return default
    h = hex_str.strip().lstrip("#")
    if len(h) == 6:
        r, g, b = h[0:2], h[2:4], h[4:6]
        return f"0x{b.upper()}{g.upper()}{r.upper()}"
    return default


def generate_weasel_custom_yaml(config):
    """根据配置生成 weasel.custom.yaml"""
    font_face = config.get("font_face", "PingFang SC Bold, PingFang SC Medium, PingFang SC, Microsoft YaHei UI, Segoe UI")
    font_point = config.get("font_point", 12)
    horizontal = "true" if config.get("horizontal", True) else "false"
    color_scheme = config.get("color_scheme", "mac_minimal_dark")

    custom_colors = config.get("custom_colors", {})
    c_back = hex_to_weasel_color(custom_colors.get("back_color", "#1E1E20"), "0x201E1E")
    c_border = hex_to_weasel_color(custom_colors.get("border_color", "#2C2C30"), "0x302C2C")
    c_hilite_back = hex_to_weasel_color(custom_colors.get("hilited_candidate_back_color", "#3C3C42"), "0x423C3C")
    c_hilite_text = hex_to_weasel_color(custom_colors.get("hilited_candidate_text_color", "#FFFFFF"), "0xFFFFFF")
    c_cand_text = hex_to_weasel_color(custom_colors.get("candidate_text_color", "#D8D8DC"), "0xDCD8D8")
    c_label = hex_to_weasel_color(custom_colors.get("label_color", "#787880"), "0x807878")

    custom_block = f"""
  "preset_color_schemes/custom":
    name: "User Custom / 自由自定义配色"
    author: "User"
    back_color: {c_back}
    border_color: {c_border}
    shadow_color: 0x60000000
    text_color: {c_cand_text}
    hilited_text_color: {c_hilite_text}
    hilited_back_color: {c_back}
    candidate_text_color: {c_cand_text}
    label_color: {c_label}
    comment_text_color: {c_label}
    hilited_candidate_back_color: {c_hilite_back}
    hilited_candidate_text_color: {c_hilite_text}
    hilited_candidate_label_color: {c_hilite_text}
    hilited_comment_text_color: {c_label}""" if color_scheme == "custom" else ""

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

  "preset_color_schemes/macos_monterey":
    name: "macOS Monterey / 深空蓝夜"
    author: "Apple"
    back_color: 0x221916
    border_color: 0x382A22
    shadow_color: 0x60000000
    text_color: 0xFFFFFF
    hilited_text_color: 0xFFFFFF
    hilited_back_color: 0x221916
    candidate_text_color: 0xD8D2D0
    label_color: 0x887870
    comment_text_color: 0x887870
    hilited_candidate_back_color: 0xFFA50A
    hilited_candidate_text_color: 0xFFFFFF
    hilited_candidate_label_color: 0xFFFFFF
    hilited_comment_text_color: 0xFFE0B0

  "preset_color_schemes/catppuccin_mocha":
    name: "Catppuccin Mocha / 莫卡暗夜"
    author: "Catppuccin"
    back_color: 0x2E1E1E
    border_color: 0x473B31
    shadow_color: 0x60000000
    text_color: 0xF5E0C6
    hilited_text_color: 0xFFFFFF
    hilited_back_color: 0x2E1E1E
    candidate_text_color: 0xEDE0CD
    label_color: 0x8C7C6C
    comment_text_color: 0x8C7C6C
    hilited_candidate_back_color: 0x5A4745
    hilited_candidate_text_color: 0xFFFFFF
    hilited_candidate_label_color: 0xF5E0C6
    hilited_comment_text_color: 0xFEB4BE

  "preset_color_schemes/tokyo_night":
    name: "Tokyo Night / 东京之夜"
    author: "TokyoNight"
    back_color: 0x261B1A
    border_color: 0x3E2C24
    shadow_color: 0x60000000
    text_color: 0xE0D0C0
    hilited_text_color: 0xFFFFFF
    hilited_back_color: 0x261B1A
    candidate_text_color: 0xD5C0A9
    label_color: 0x7E6856
    comment_text_color: 0x7E6856
    hilited_candidate_back_color: 0x573428
    hilited_candidate_text_color: 0xFFFFFF
    hilited_candidate_label_color: 0xD0E0FF
    hilited_comment_text_color: 0xDDBA7A

  "preset_color_schemes/nord_dark":
    name: "Nord Dark / 北极极光"
    author: "Arctic"
    back_color: 0x40342E
    border_color: 0x4C433B
    shadow_color: 0x60000000
    text_color: 0xECE8E5
    hilited_text_color: 0xFFFFFF
    hilited_back_color: 0x40342E
    candidate_text_color: 0xE6DFD8
    label_color: 0x907C61
    comment_text_color: 0x907C61
    hilited_candidate_back_color: 0x5E4C43
    hilited_candidate_text_color: 0xFFFFFF
    hilited_candidate_label_color: 0xE5E8EC
    hilited_comment_text_color: 0xD0C088

  "preset_color_schemes/sakura_pink":
    name: "Sakura Pink / 樱花浅粉"
    author: "Sakura"
    back_color: 0xF8F5FF
    border_color: 0xE8D5E5
    shadow_color: 0x30000000
    text_color: 0x3B2030
    hilited_text_color: 0x301525
    hilited_back_color: 0xF8F5FF
    candidate_text_color: 0x5C404E
    label_color: 0x9A808C
    comment_text_color: 0x9A808C
    hilited_candidate_back_color: 0xDCBEE8
    hilited_candidate_text_color: 0x301525
    hilited_candidate_label_color: 0x5C404E
    hilited_comment_text_color: 0x8C4070
{custom_block}
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
    for item in ["default.custom.yaml", "wanxiang.custom.yaml", "weasel.custom.yaml", "custom_phrase.dict.yaml"]:
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
