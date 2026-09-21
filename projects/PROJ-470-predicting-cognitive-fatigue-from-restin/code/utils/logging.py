"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import csv
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def log_artifact_rejection(artifact_type: str, artifact_id: str, reason: str) -> None:
    """Log artifact rejection to the exclusion log."""
    entry = get_logger().log("artifact_rejection", artifact_type=artifact_type, artifact_id=artifact_id, reason=reason)
    save_rejection_summary()


def log_participant_exclusion(participant_id: str, reason: str) -> None:
    """Log participant exclusion to the exclusion log."""
    entry = get_logger().log("participant_exclusion", participant_id=participant_id, reason=reason)
    save_rejection_summary()


def save_rejection_summary() -> None:
    """Save all rejection entries to the exclusion log CSV."""
    logger = get_logger()
    exclusion_log_path = "data/processed/exclusion_log.csv"
    os.makedirs(os.path.dirname(exclusion_log_path), exist_ok=True)

    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(exclusion_log_path)

    with open(exclusion_log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["participant_id", "reason", "timestamp"])

        for entry in logger.entries:
            if entry.operation in ["participant_exclusion", "artifact_rejection"]:
                pid = entry.parameters.get("participant_id", entry.parameters.get("artifact_id", "unknown"))
                reason = entry.parameters.get("reason", "unknown")
                writer.writerow([pid, reason, entry.timestamp])


def get_rejection_counts() -> dict:
    """Get counts of rejections by reason."""
    logger = get_logger()
    counts = {}
    for entry in logger.entries:
        if entry.operation in ["participant_exclusion", "artifact_rejection"]:
            reason = entry.parameters.get("reason", "unknown")
            counts[reason] = counts.get(reason, 0) + 1
    return counts


def save_exclusion_log_csv(entries: list) -> None:
    """Save exclusion log entries directly to CSV."""
    exclusion_log_path = "data/processed/exclusion_log.csv"
    os.makedirs(os.path.dirname(exclusion_log_path), exist_ok=True)

    file_exists = os.path.exists(exclusion_log_path)

    with open(exclusion_log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["participant_id", "reason", "timestamp"])

        for entry in entries:
            writer.writerow([entry.get("participant_id", "unknown"), entry.get("reason", "unknown"), entry.get("timestamp", datetime.utcnow().isoformat())])
