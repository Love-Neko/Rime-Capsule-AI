from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RemoteError(RuntimeError):
    pass


def post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read(500).decode("utf-8", errors="replace")
        raise RemoteError(f"remote HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RemoteError(f"remote connection failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RemoteError("remote request timed out") from exc
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RemoteError("remote response was not valid JSON") from exc
    if not isinstance(result, dict):
        raise RemoteError("remote response must be a JSON object")
    return result
