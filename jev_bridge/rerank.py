from __future__ import annotations

import time
from typing import Any

from .config import Settings, settings
from .json_http import RemoteError, post_json
from .local_ranker import LocalStore, default_store_path, rank_locally
from .ollama import ollama_ranker
from .safety import contains_sensitive_text


def _choice_answer(response: dict[str, Any], question_id: str) -> tuple[str | None, float | None, dict[str, float]]:
    answer = (response.get("answers") or {}).get(question_id) or {}
    selected = answer.get("choice") or answer.get("selected")
    confidence = answer.get("confidence")
    probabilities = answer.get("probabilities") or answer.get("probability") or {}
    if not isinstance(probabilities, dict):
        probabilities = {}
    clean_probabilities: dict[str, float] = {}
    for key, value in probabilities.items():
        try:
            clean_probabilities[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None
    return (str(selected) if selected is not None else None, confidence, clean_probabilities)


_MEM_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_MAX_SIZE = 1000
_CACHE_TTL = 300.0  # 5 minutes


def _get_cache(key: str) -> dict[str, Any] | None:
    item = _MEM_CACHE.get(key)
    if not item:
        return None
    created_at, val = item
    if time.time() - created_at > _CACHE_TTL:
        _MEM_CACHE.pop(key, None)
        return None
    return val


def _set_cache(key: str, val: dict[str, Any]) -> None:
    if len(_MEM_CACHE) > _CACHE_MAX_SIZE:
        keys = list(_MEM_CACHE.keys())[:200]
        for k in keys:
            _MEM_CACHE.pop(k, None)
    _MEM_CACHE[key] = (time.time(), val)


def clear_cache() -> None:
    _MEM_CACHE.clear()


_PERSISTENT_CLIENT: Any = None
_PERSISTENT_KEY: str = ""


def _get_persistent_client(settings_: Settings) -> Any:
    global _PERSISTENT_CLIENT, _PERSISTENT_KEY
    key = settings_.typesafe_api_key
    if not key:
        return None
    if _PERSISTENT_CLIENT is None or _PERSISTENT_KEY != key:
        try:
            from typesafe_sdk import TypeSafeClient

            _PERSISTENT_CLIENT = TypeSafeClient(
                api_key=key,
                base_url=settings_.typesafe_base_url,
                timeout=settings_.typesafe_timeout,
            )
            _PERSISTENT_KEY = key
        except Exception:
            _PERSISTENT_CLIENT = None
    return _PERSISTENT_CLIENT


def rerank_candidates(
    *, context: str, pinyin: str, candidates: list[str], settings_: Settings = settings, use_cache: bool = True
) -> dict[str, Any]:
    original = list(dict.fromkeys(candidate.strip() for candidate in candidates if candidate.strip()))
    if not original:
        return {"candidates": [], "selected": None, "confidence": None, "jev_used": False, "tag": ""}
    if contains_sensitive_text(context):
        return {
            "candidates": original,
            "selected": original[0],
            "confidence": None,
            "jev_used": False,
            "tag": "",
            "reason": "sensitive-looking context was blocked",
        }

    key_fingerprint = settings_.typesafe_api_key[:8] if settings_.typesafe_api_key else "nokey"
    cache_key = f"{key_fingerprint}|{context[-60:]}|{pinyin}|{','.join(original[:10])}"
    if use_cache:
        cached = _get_cache(cache_key)
        if cached is not None:
            return {**cached, "cache_hit": True}

    store = LocalStore(settings_.local_db_path or default_store_path())
    local = rank_locally(context=context, pinyin=pinyin, candidates=original, store=store)

    if not settings_.typesafe_api_key:
        semantic = ollama_ranker.cached(context=context, pinyin=pinyin, candidates=original)
        if semantic and semantic.get("selected") in original:
            selected = semantic["selected"]
            ordered = [selected] + [item for item in original if item != selected]
            res = {
                **local,
                "candidates": ordered,
                "selected": selected,
                "tag": "",
                "ollama_used": True,
                "ollama_pending": False,
                "ollama_model": semantic.get("model"),
                "confidence": None,
                "jev_used": False,
                "reason": "local rules + cached Ollama ranking",
            }
            _set_cache(cache_key, res)
            return res
        ollama_ranker.request(context=context, pinyin=pinyin, candidates=original)
        res = {
            **local,
            "confidence": None,
            "jev_used": False,
            "tag": "",
            "ollama_used": False,
            "ollama_pending": ollama_ranker.enabled,
            "reason": "local ranker (Jev is disabled)",
        }
        _set_cache(cache_key, res)
        return res

    eval_candidates = original[:6]
    criteria = {candidate: candidate for candidate in eval_candidates}
    started = time.perf_counter()
    selected: str | None = None
    confidence: float | None = None
    probabilities: dict[str, float] = {}

    # 1. Try typesafe-sdk with persistent client connection pooling (ultra-fast)
    sdk_used = False
    client = _get_persistent_client(settings_)
    if client is not None:
        try:
            from typesafe_sdk import Choice

            resp = client.system_one(
                state={
                    "context": context[-settings_.context_chars :],
                    "pinyin": pinyin,
                    "candidates": eval_candidates,
                },
                model=settings_.typesafe_model,
                questions={
                    "best_candidate": Choice(
                        instructions="你是中文输入法候选重排器。请结合光标前上下文，从candidates中选出最符合当前语境的词并排在第一位。",
                        criteria=criteria,
                    )
                },
            )
            answer = resp.answers.get("best_candidate")
            if answer:
                selected = getattr(answer, "choice", None)
                confidence = getattr(answer, "confidence", None)
                raw_prob = getattr(answer, "probabilities", {}) or {}
                probabilities = {str(k): float(v) for k, v in raw_prob.items() if v is not None}
                sdk_used = True
        except Exception:
            sdk_used = False

    # 2. Fallback to direct HTTP post_json if SDK failed or wasn't used
    if not sdk_used:
        payload = {
            "state": {
                "context": context[-settings_.context_chars :],
                "pinyin": pinyin,
                "candidates": original,
            },
            "model": settings_.typesafe_model,
            "questions": {
                "best_candidate": {
                    "type": "choice",
                    "instructions": (
                        "你是中文输入法候选重排器。对当前列表中的所有候选进行比较，选择结合光标前上下文后"
                        "用户最可能想输入的一项，并把它排在第一位。重点考虑词语搭配、句法、语义、常识、"
                        "已经输入的句子和拼音；不能只按词频，也不能只看单个词。必须只能从 candidates 中选择，"
                        "不能创造、改写、合并或删除候选。这个规则适用于任意数量的候选和任意拼音，不是只针对示例词。"
                    ),
                    "criteria": criteria,
                }
            },
        }
        try:
            response = post_json(
                settings_.typesafe_base_url.rstrip("/") + "/v1/systemone",
                payload,
                headers={"Authorization": f"Bearer {settings_.typesafe_api_key}"},
                timeout=settings_.typesafe_timeout,
            )
            selected, confidence, probabilities = _choice_answer(response, "best_candidate")
        except RemoteError as exc:
            return {
                **local,
                "confidence": None,
                "jev_used": False,
                "tag": "",
                "ollama_used": False,
                "ollama_pending": False,
                "reason": f"Jev unavailable; local fallback: {exc}",
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            }

    ordered = original[:]
    if selected in ordered:
        ordered.remove(selected)
        ordered.insert(0, selected)
    elif probabilities:
        ordered.sort(key=lambda item: probabilities.get(item, -1.0), reverse=True)
        selected = ordered[0]

    jev_used = bool(selected in original)
    result = {
        "candidates": ordered,
        "selected": selected,
        "tag": "✦ Jev" if jev_used else "",
        "confidence": confidence,
        "probabilities": probabilities,
        "jev_used": jev_used,
        "local_used": True,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }
    _set_cache(cache_key, result)
    return result
