#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
万象拼音 400MB 语法模型高速下载工具
支持多镜像、断点续传、实时进度追踪
"""

import os
import sys
import time
import urllib.request
from pathlib import Path

MODEL_FILENAME = "wanxiang-lts-zh-hans.gram"
MODEL_URLS = [
    f"https://github.com/amzxyz/rime-wanxiang/releases/download/v18.0.9/{MODEL_FILENAME}",
    f"https://ghproxy.net/https://github.com/amzxyz/rime-wanxiang/releases/download/v18.0.9/{MODEL_FILENAME}",
]
EXPECTED_SIZE = 419910700  # ~400MB


def get_default_dest():
    appdata = os.environ.get("APPDATA")
    if appdata:
        rime_dir = Path(appdata) / "Rime"
        rime_dir.mkdir(parents=True, exist_ok=True)
        return rime_dir / MODEL_FILENAME
    return Path(__file__).resolve().parent.parent / "rime_config" / MODEL_FILENAME


def download_grammar_model(dest_path=None, progress_callback=None):
    if dest_path is None:
        dest_path = get_default_dest()
    dest_path = Path(dest_path)

    # 检查是否已完整存在
    if dest_path.exists() and dest_path.stat().st_size >= EXPECTED_SIZE - 1024:
        if progress_callback:
            progress_callback(100.0, dest_path.stat().st_size, EXPECTED_SIZE, "模型已存在且完整")
        return True, f"模型已存在：{dest_path} ({dest_path.stat().st_size / (1024*1024):.1f} MB)"

    temp_path = dest_path.with_suffix(".gram.downloading")
    downloaded = 0
    if temp_path.exists():
        downloaded = temp_path.stat().st_size

    last_error = ""
    for url in MODEL_URLS:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
                }
            )
            if downloaded > 0:
                req.add_header("Range", f"bytes={downloaded}-")

            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status if hasattr(resp, "status") else 200
                total_size = EXPECTED_SIZE
                content_len = resp.headers.get("Content-Length")
                if content_len:
                    if status == 206:
                        total_size = downloaded + int(content_len)
                    else:
                        downloaded = 0
                        total_size = int(content_len)

                mode = "ab" if downloaded > 0 and status == 206 else "wb"
                with open(temp_path, mode) as f:
                    chunk_size = 1024 * 512  # 512 KB
                    last_update = time.time()
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_update > 0.5 or downloaded >= total_size:
                            last_update = now
                            pct = min(100.0, (downloaded / total_size) * 100) if total_size > 0 else 0
                            if progress_callback:
                                progress_callback(pct, downloaded, total_size, "正在下载...")
                            else:
                                print(f"\r下载进度: {pct:.1f}% ({downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB)", end="", flush=True)

            if temp_path.exists() and temp_path.stat().st_size >= EXPECTED_SIZE - 2048:
                if dest_path.exists():
                    dest_path.unlink()
                temp_path.rename(dest_path)
                msg = f"下载完成！已保存到：{dest_path}"
                if progress_callback:
                    progress_callback(100.0, total_size, total_size, "下载成功")
                return True, msg
        except Exception as e:
            last_error = str(e)
            continue

    return False, f"下载失败：{last_error}"


if __name__ == "__main__":
    print("开始下载万象拼音 400MB 语法模型...")
    ok, msg = download_grammar_model()
    print(f"\n{msg}")
    sys.exit(0 if ok else 1)
