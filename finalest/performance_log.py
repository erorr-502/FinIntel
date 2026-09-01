"""Tiny JSONL persistence layer for FININTEL session metrics."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent / "data" / "session_log.jsonl"


def append_run(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.now().isoformat(timespec="seconds"), **record}
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_runs(limit: int = 100) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]
