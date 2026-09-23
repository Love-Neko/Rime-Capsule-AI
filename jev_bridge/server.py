from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .completion import complete
from .config import settings
from .rerank import rerank_candidates
from .local_ranker import LocalStore, default_store_path
from .ollama import ollama_ranker


def _json_error(message: str) -> tuple[int, dict[str, Any]]:
    return 400, {"error": message}


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalRimeBridge/0.2"

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._send(200, {"ok": True, "typesafe_configured": bool(settings.typesafe_api_key), "ollama": ollama_ranker.status()})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        if length > 128 * 1024:
            self._send(413, {"error": "request too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(*_json_error("body must be valid JSON"))
            return
        if not isinstance(payload, dict):
            self._send(*_json_error("body must be a JSON object"))
            return
        if self.path == "/v1/rerank":
            context = payload.get("context", "")
            pinyin = payload.get("pinyin", "")
            candidates = payload.get("candidates", [])
            if not isinstance(context, str) or not isinstance(pinyin, str):
                self._send(*_json_error("context and pinyin must be strings"))
                return
            if not isinstance(candidates, list) or not all(isinstance(item, str) for item in candidates):
                self._send(*_json_error("candidates must be an array of strings"))
                return
            self._send(200, rerank_candidates(context=context, pinyin=pinyin, candidates=candidates))
            return
        if self.path == "/v1/complete":
            before = payload.get("before", "")
            after = payload.get("after", "")
            language = payload.get("language", "zh-CN")
            if not all(isinstance(value, str) for value in (before, after, language)):
                self._send(*_json_error("before, after and language must be strings"))
                return
            self._send(200, complete(before=before, after=after, language=language))
            return
        if self.path == "/v1/feedback":
            context = payload.get("context", "")
            pinyin = payload.get("pinyin", "")
            candidate = payload.get("candidate", "")
            if not all(isinstance(value, str) for value in (context, pinyin, candidate)):
                self._send(*_json_error("context, pinyin and candidate must be strings"))
                return
            if not candidate.strip():
                self._send(*_json_error("candidate must not be empty"))
                return
            LocalStore(settings.local_db_path or default_store_path()).record(
                context=context, pinyin=pinyin, candidate=candidate
            )
            self._send(200, {"ok": True, "stored": True})
            return
        self._send(404, {"error": "not found"})


def run() -> None:
    address = (settings.host, settings.port)
    print(f"Local Rime bridge listening on http://{settings.host}:{settings.port}")
    print(f"Ollama semantic ranking: {'enabled' if ollama_ranker.enabled else 'disabled'}")
    from .ipc_watcher import start_ipc_watcher
    start_ipc_watcher()
    print("Zero-lag IPC file watcher: active (listening for Rime Tab triggers)")
    ThreadingHTTPServer(address, Handler).serve_forever()


if __name__ == "__main__":
    run()
