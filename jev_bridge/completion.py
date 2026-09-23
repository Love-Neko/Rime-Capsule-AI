from __future__ import annotations

import re
import time
from typing import Any

from .config import Settings, settings
from .json_http import RemoteError, post_json
from .safety import contains_sensitive_text


def _extract_text(response: dict[str, Any]) -> str:
    # Ollama's native API exposes the non-thinking answer in message.content;
    # its OpenAI compatibility layer may put the answer in reasoning instead.
    if isinstance(response.get("message"), dict):
        message = response["message"]
        return str(message.get("content") or "").strip()
    choices = response.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message") or {}
    text = message.get("content") or choices[0].get("text") or ""
    if isinstance(text, list):
        text = "".join(item.get("text", "") for item in text if isinstance(item, dict))
    return str(text).strip()


def _clean_completion(text: str, max_chars: int = 160) -> str:
    text = text.replace("\r", "").replace("\n", " ").strip()
    text = re.sub(r"^(补全|建议|completion)\s*[:：]\s*", "", text, flags=re.I)
    return text[:max_chars].rstrip()


def complete(*, before: str, after: str = "", language: str = "zh-CN", settings_: Settings = settings) -> dict[str, Any]:
    before = before[-settings_.context_chars :]
    after = after[:300]
    if not before.strip():
        return {"completion": "", "used": False, "reason": "empty context"}
    if contains_sensitive_text(before) or contains_sensitive_text(after):
        return {"completion": "", "used": False, "reason": "sensitive-looking context was blocked"}
    if not settings_.completion_base_url or not settings_.completion_model:
        return {"completion": "", "used": False, "reason": "completion model is not configured"}

    payload = {
        "model": settings_.completion_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是中文输入法的 Tab 补全器。只返回光标后面应该补上的短文本，"
                    "不要解释，不要引号，不要 Markdown，不要重复已有文字。"
                ),
            },
            {
                "role": "user",
                "content": f"语言：{language}\n光标前：{before}\n光标后：{after}\n请给出后续补全文本。",
            },
        ],
        "temperature": 0.2,
        "max_tokens": settings_.completion_max_tokens,
        "stream": False,
    }
    headers = {}
    if settings_.completion_api_key:
        headers["Authorization"] = f"Bearer {settings_.completion_api_key}"
    started = time.perf_counter()
    try:
        base = settings_.completion_base_url.rstrip("/")
        is_ollama = "127.0.0.1:11434" in base or "localhost:11434" in base
        if is_ollama:
            # Native Ollama API supports think=false for Qwen3 and avoids
            # returning only hidden reasoning tokens for short completions.
            url = "http://127.0.0.1:11434/api/chat"
            payload["think"] = False
            payload["keep_alive"] = "10m"
        else:
            url = base + "/chat/completions"
        response = post_json(
            url,
            payload,
            headers=headers,
            timeout=settings_.completion_timeout,
        )
        text = _clean_completion(_extract_text(response))
    except RemoteError as exc:
        return {
            "completion": "",
            "used": False,
            "reason": str(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    return {
        "completion": text,
        "used": bool(text),
        "model": settings_.completion_model,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }
