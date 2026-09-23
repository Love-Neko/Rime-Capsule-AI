from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .config import Settings, settings
from .json_http import RemoteError, post_json


class OllamaRanker:
    """Asynchronous local semantic ranker.

    Ranking must not block a keystroke. The first request returns the local
    rule/SQLite result and starts an Ollama request; a later identical request
    can use the cached semantic result.
    """

    def __init__(self, settings_: Settings) -> None:
        self.settings = settings_
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ollama-ranker")
        self._lock = threading.Lock()
        self._cache: dict[str, dict[str, Any]] = {}
        self._pending: set[str] = set()
        self._failures: dict[str, str] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.settings.local_ollama_enabled and self.settings.local_ollama_base_url)

    def _key(self, *, context: str, pinyin: str, candidates: list[str]) -> str:
        return json.dumps(
            {"context": context[-300:], "pinyin": pinyin, "candidates": candidates},
            ensure_ascii=False,
            sort_keys=True,
        )

    def cached(self, *, context: str, pinyin: str, candidates: list[str]) -> dict[str, Any] | None:
        with self._lock:
            return self._cache.get(self._key(context=context, pinyin=pinyin, candidates=candidates))

    def request(self, *, context: str, pinyin: str, candidates: list[str]) -> None:
        if not self.enabled:
            return
        key = self._key(context=context, pinyin=pinyin, candidates=candidates)
        with self._lock:
            if key in self._cache or key in self._pending:
                return
            self._pending.add(key)
        self._executor.submit(self._run, key, context, pinyin, candidates)

    def _run(self, key: str, context: str, pinyin: str, candidates: list[str]) -> None:
        try:
            criteria = "、".join(candidates)
            prompt = (
                "你是中文输入法候选重排器。只从候选列表中选择一个最符合上下文的词。"
                "不要输出解释，只输出 JSON，例如 {\"choice\":\"油箱\"}。\n"
                f"上下文：{context[-300:]}\n拼音：{pinyin}\n候选：{criteria}"
            )
            response = post_json(
                self.settings.local_ollama_base_url.rstrip("/") + "/api/chat",
                {
                    "model": self.settings.local_ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "format": "json",
                    "think": False,
                    "keep_alive": "10m",
                    "options": {"temperature": 0},
                },
                headers={},
                timeout=self.settings.local_ollama_timeout,
            )
            content = ((response.get("message") or {}).get("content") or "").strip()
            parsed = json.loads(content)
            choice = parsed.get("choice") if isinstance(parsed, dict) else None
            if choice not in candidates:
                raise ValueError("Ollama returned a choice outside the candidate list")
            with self._lock:
                self._cache[key] = {"selected": choice, "model": self.settings.local_ollama_model}
                self._failures.pop(key, None)
        except (RemoteError, ValueError, TypeError, json.JSONDecodeError) as exc:
            with self._lock:
                self._failures[key] = str(exc)
        finally:
            with self._lock:
                self._pending.discard(key)

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.enabled,
                "model": self.settings.local_ollama_model,
                "pending": len(self._pending),
                "cached": len(self._cache),
                "failures": len(self._failures),
            }


ollama_ranker = OllamaRanker(settings)
