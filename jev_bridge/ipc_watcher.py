from __future__ import annotations

import os
import tempfile
import threading
import time

from .rerank import rerank_candidates

REQ_FILE = os.path.join(tempfile.gettempdir(), "rime_jev_req.txt")
RES_FILE = os.path.join(tempfile.gettempdir(), "rime_jev_res.txt")


def start_ipc_watcher() -> threading.Thread:
    def _loop() -> None:
        # Pre-warm connection to TypeSafe API in background
        try:
            rerank_candidates(context="预热", pinyin="yu're", candidates=["预热", "鱼热"])
        except Exception:
            pass

        last_mtime = 0.0
        while True:
            time.sleep(0.02)
            if not os.path.exists(REQ_FILE):
                continue
            try:
                mtime = os.path.getmtime(REQ_FILE)
                if mtime <= last_mtime:
                    continue
                last_mtime = mtime
                # 25ms debounce
                time.sleep(0.025)
                new_mtime = os.path.getmtime(REQ_FILE)
                if new_mtime > mtime:
                    continue

                with open(REQ_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                lines = content.splitlines()
                if len(lines) < 3:
                    continue
                context = lines[0].strip()
                pinyin = lines[1].strip()
                candidates = [c.strip() for c in lines[2].split(",") if c.strip()]
                if not pinyin or not candidates:
                    continue

                res = rerank_candidates(context=context, pinyin=pinyin, candidates=candidates)
                selected = res.get("selected", "")
                tag = res.get("tag", "✦ Jev")

                tmp_res = RES_FILE + ".tmp"
                with open(tmp_res, "w", encoding="utf-8") as f:
                    f.write(f"pinyin={pinyin}\nselected={selected}\ntag={tag}\n")
                os.replace(tmp_res, RES_FILE)
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True, name="JevIpcWatcher")
    t.start()
    return t
