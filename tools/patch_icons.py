#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小狼毫现代 macOS 极简胶囊托盘图标一键注入工具
将系统托盘的老旧印章中/方块A全面更新为现代 macOS 胶囊蓝“中”与深空灰“A”
"""

import os
import sys
import struct
import ctypes
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"

kernel32 = ctypes.windll.kernel32
RT_ICON = 3
RT_GROUP_ICON = 14


def parse_ico(ico_bytes):
    reserved, type_, count = struct.unpack('<HHH', ico_bytes[:6])
    entries = []
    offset = 6
    for i in range(count):
        width, height, colors, res, planes, bpp, size, img_offset = struct.unpack('<BBBBHHII', ico_bytes[offset:offset+16])
        data = ico_bytes[img_offset:img_offset+size]
        entries.append({
            'width': width if width != 0 else 256,
            'height': height if height != 0 else 256,
            'colors': colors,
            'planes': planes,
            'bpp': bpp,
            'size': size,
            'data': data
        })
        offset += 16
    return entries


def patch_file(target_dll, zh_ico_data, en_ico_data):
    if not os.path.exists(target_dll):
        return False, f"目标文件不存在：{target_dll}"

    zh_entries = parse_ico(zh_ico_data)
    en_entries = parse_ico(en_ico_data)

    hUpdate = kernel32.BeginUpdateResourceW(target_dll, False)
    if not hUpdate:
        return False, f"无法打开文件写入资源（可能权限不足）：{target_dll}"

    try:
        # Update EN (Group 101)
        en_header = bytearray(struct.pack('<HHH', 0, 1, len(en_entries)))
        for i, entry in enumerate(en_entries):
            icon_id = 1000 + i + 1
            w = entry['width'] if entry['width'] < 256 else 0
            h = entry['height'] if entry['height'] < 256 else 0
            en_header.extend(struct.pack('<BBBBHHIH', w, h, entry['colors'], 0, entry['planes'], entry['bpp'], entry['size'], icon_id))
            kernel32.UpdateResourceW(hUpdate, RT_ICON, icon_id, 0x0409, entry['data'], len(entry['data']))
        kernel32.UpdateResourceW(hUpdate, RT_GROUP_ICON, 101, 0x0409, bytes(en_header), len(en_header))

        # Update ZH (Group 102)
        zh_header = bytearray(struct.pack('<HHH', 0, 1, len(zh_entries)))
        for i, entry in enumerate(zh_entries):
            icon_id = 2000 + i + 1
            w = entry['width'] if entry['width'] < 256 else 0
            h = entry['height'] if entry['height'] < 256 else 0
            zh_header.extend(struct.pack('<BBBBHHIH', w, h, entry['colors'], 0, entry['planes'], entry['bpp'], entry['size'], icon_id))
            kernel32.UpdateResourceW(hUpdate, RT_ICON, icon_id, 0x0409, entry['data'], len(entry['data']))
        kernel32.UpdateResourceW(hUpdate, RT_GROUP_ICON, 102, 0x0409, bytes(zh_header), len(zh_header))

        success = kernel32.EndUpdateResourceW(hUpdate, False)
        return bool(success), f"已成功更新图标：{target_dll}"
    except Exception as e:
        kernel32.EndUpdateResourceW(hUpdate, True)
        return False, f"更新资源异常：{str(e)}"


def run_patch():
    zh_path = ASSETS_DIR / "zh_modern.ico"
    en_path = ASSETS_DIR / "en_modern.ico"
    if not zh_path.exists() or not en_path.exists():
        return False, "图标资源文件缺失（assets/zh_modern.ico 或 en_modern.ico 不存在）"

    zh_data = zh_path.read_bytes()
    en_data = en_path.read_bytes()

    targets = [
        r"C:\Program Files\Rime\weasel-0.17.4\weasel.dll",
        r"C:\Program Files\Rime\weasel-0.17.4\weaselx64.dll",
        r"C:\Program Files\Rime\weasel-0.17.4\WeaselServer.exe",
        r"C:\Windows\System32\weasel.dll",
        r"C:\Windows\SysWOW64\weasel.dll",
    ]

    results = []
    for tgt in targets:
        if os.path.exists(tgt):
            ok, msg = patch_file(tgt, zh_data, en_data)
            results.append((tgt, ok, msg))

    return True, results


if __name__ == "__main__":
    ok, res = run_patch()
    for tgt, s, m in res:
        print(f"[{'OK' if s else 'SKIP'}] {tgt}: {m}")
