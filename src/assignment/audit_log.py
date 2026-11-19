"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import time
import uuid


def default_audit_log_path() -> str:
    """Always resolve to <repo>/outputs/… (safe when cwd is src/)."""
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / "outputs" / "audit_log.json")


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        """Record an input and start a latency timer for the request."""
        key = request_id or uuid.uuid4().hex
        if key in self._open:
            raise ValueError(f"Request is already open in audit log: {key}")

        entry = {
            "request_id": key,
            "user_id": user_id,
            "input": text,
            "started_at": utc_now_iso(),
            "output": None,
            "completed_at": None,
            "blocked": None,
            "layer": None,
            "latency_ms": None,
        }
        self.logs.append(entry)
        self._open[key] = {
            "index": len(self.logs) - 1,
            "started": time.perf_counter(),
        }
        return key

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
    ):
        """Complete the matching request record with its result and latency."""
        key = request_id
        if key is None:
            key = next(
                (
                    candidate
                    for candidate, opened in reversed(list(self._open.items()))
                    if self.logs[opened["index"]]["user_id"] == user_id
                ),
                None,
            )

        opened = self._open.pop(key, None) if key is not None else None
        if opened is None:
            entry = {
                "request_id": key or uuid.uuid4().hex,
                "user_id": user_id,
                "input": None,
                "started_at": None,
                "output": text,
                "completed_at": utc_now_iso(),
                "blocked": blocked,
                "layer": layer,
                "latency_ms": None,
            }
            self.logs.append(entry)
            return

        entry = self.logs[opened["index"]]
        entry.update(
            {
                "output": text,
                "completed_at": utc_now_iso(),
                "blocked": blocked,
                "layer": layer,
                "latency_ms": round(
                    (time.perf_counter() - opened["started"]) * 1000, 3
                ),
            }
        )

    def export_json(self, filepath: str | None = None):
        """Write logs to disk (JSON array) under repo-root ``outputs/`` by default."""
        path = Path(filepath or default_audit_log_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
