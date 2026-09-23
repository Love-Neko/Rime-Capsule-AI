from __future__ import annotations

import re


_SENSITIVE = re.compile(
    r"(?i)(?:password|passwd|密码|secret|api[_ -]?key|token|bearer)\s*[:=]\s*\S+|"
    r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b|"
    r"\bsk-[A-Za-z0-9_-]{20,}\b"
)


def contains_sensitive_text(value: str) -> bool:
    return bool(_SENSITIVE.search(value))
