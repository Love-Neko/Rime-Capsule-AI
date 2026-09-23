from __future__ import annotations

import os
from dataclasses import dataclass


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8765
    typesafe_base_url: str = "https://api.typesafe.ai"
    typesafe_api_key: str = ""
    typesafe_model: str = "jev-latest"
    typesafe_timeout: float = 5.0
    local_db_path: str = ""
    local_ollama_enabled: bool = False
    local_ollama_base_url: str = "http://127.0.0.1:11434"
    local_ollama_model: str = "qwen2.5:3b"
    local_ollama_timeout: float = 20.0
    completion_base_url: str = ""
    completion_api_key: str = ""
    completion_model: str = "qwen2.5:3b"
    completion_timeout: float = 0.8
    completion_max_tokens: int = 48
    context_chars: int = 1200


def load_settings() -> Settings:
    return Settings(
        host=os.getenv("JEV_BRIDGE_HOST", "127.0.0.1"),
        port=int(os.getenv("JEV_BRIDGE_PORT", "8765")),
        typesafe_base_url=os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai"),
        typesafe_api_key=os.getenv("TYPESAFE_API_KEY", ""),
        typesafe_model=os.getenv("TYPESAFE_DEFAULT_MODEL", "jev-latest"),
        typesafe_timeout=_float_env("TYPESAFE_TIMEOUT_SECONDS", 5.0),
        local_db_path=os.getenv("LOCAL_RANKER_DB_PATH", ""),
        local_ollama_enabled=os.getenv("LOCAL_OLLAMA_ENABLED", "0").lower() in {"1", "true", "yes", "on"},
        local_ollama_base_url=os.getenv("LOCAL_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        local_ollama_model=os.getenv("LOCAL_OLLAMA_MODEL", "qwen2.5:3b"),
        local_ollama_timeout=_float_env("LOCAL_OLLAMA_TIMEOUT_SECONDS", 20.0),
        completion_base_url=os.getenv("TAB_COMPLETION_BASE_URL", ""),
        completion_api_key=os.getenv("TAB_COMPLETION_API_KEY", ""),
        completion_model=os.getenv("TAB_COMPLETION_MODEL", "qwen2.5:3b"),
        completion_timeout=_float_env("TAB_COMPLETION_TIMEOUT_SECONDS", 0.8),
        completion_max_tokens=int(os.getenv("TAB_COMPLETION_MAX_TOKENS", "48")),
        context_chars=int(os.getenv("COMPLETION_CONTEXT_CHARS", "1200")),
    )


settings = load_settings()


def reload_settings() -> Settings:
    global settings
    settings = load_settings()
    return settings
