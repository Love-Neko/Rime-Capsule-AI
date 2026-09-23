from __future__ import annotations

import math
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any


DEFAULT_RULES: dict[str, dict[str, float]] = {
    "汽车": {"油箱": 5.0, "邮箱": -1.0},
    "发动机": {"油箱": 4.0},
    "汽油": {"油箱": 4.0},
    "加油": {"油箱": 4.0},
    "油耗": {"油箱": 3.0},
    "电子邮件": {"邮箱": 5.0},
    "邮件": {"邮箱": 4.0},
    "收件": {"邮箱": 3.0},
    "邮件地址": {"邮箱": 5.0},
    "账号": {"邮箱": 2.5},
    "登录": {"邮箱": 2.0},
    "又想": {"又想": 5.0},
    "希望": {"又想": 2.0},
}


class LocalStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        db = self._connect()
        try:
            db.execute(
                """CREATE TABLE IF NOT EXISTS selections (
                    id INTEGER PRIMARY KEY,
                    pinyin TEXT NOT NULL,
                    candidate TEXT NOT NULL,
                    context TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pinyin, candidate, context)
                )"""
            )
            db.commit()
        finally:
            db.close()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=2)
        db.row_factory = sqlite3.Row
        return db

    def record(self, *, pinyin: str, candidate: str, context: str) -> None:
        context_key = context[-80:].strip()
        with self._lock:
            db = self._connect()
            try:
                db.execute(
                """INSERT INTO selections(pinyin, candidate, context, count)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(pinyin, candidate, context)
                   DO UPDATE SET count=count+1, updated_at=CURRENT_TIMESTAMP""",
                    (pinyin, candidate, context_key),
                )
                db.commit()
            finally:
                db.close()

    def counts(self, *, pinyin: str, candidates: list[str], context: str) -> dict[str, float]:
        if not candidates:
            return {}
        context_key = context[-80:].strip()
        marks = ",".join("?" for _ in candidates)
        params: list[Any] = [pinyin, *candidates]
        with self._lock:
            db = self._connect()
            try:
                rows = db.execute(
                f"SELECT candidate, context, count FROM selections WHERE pinyin=? AND candidate IN ({marks})",
                params,
                ).fetchall()
            finally:
                db.close()
        scores = {candidate: 0.0 for candidate in candidates}
        for row in rows:
            value = math.log1p(float(row["count"]))
            scores[row["candidate"]] += value
            if row["context"] and row["context"] in context_key:
                scores[row["candidate"]] += 2.0 * value
        return scores


def default_store_path() -> str:
    root = os.getenv("LOCALAPPDATA") or os.getenv("TEMP") or "."
    return str(Path(root) / "JevWeaselBridge" / "selections.sqlite3")


def rank_locally(*, context: str, pinyin: str, candidates: list[str], store: LocalStore) -> dict[str, Any]:
    original = list(dict.fromkeys(item.strip() for item in candidates if item.strip()))
    scores = {candidate: -index * 0.05 for index, candidate in enumerate(original)}
    matched_rules: list[str] = []
    for trigger, rule_scores in DEFAULT_RULES.items():
        if trigger in context:
            matched_rules.append(trigger)
            for candidate, score in rule_scores.items():
                if candidate in scores:
                    scores[candidate] += score
    learned = store.counts(pinyin=pinyin, candidates=original, context=context)
    for candidate, score in learned.items():
        scores[candidate] += score
    ordered = sorted(original, key=lambda item: scores[item], reverse=True)
    return {
        "candidates": ordered,
        "selected": ordered[0] if ordered else None,
        "scores": {candidate: round(scores[candidate], 4) for candidate in ordered},
        "matched_rules": matched_rules,
        "learned": any(value > 0 for value in learned.values()),
        "local_used": True,
    }
