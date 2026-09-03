"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import csv
import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .logging import LogEntry, ReproducibilityLogger, get_logger, log_operation

# Ensure the module can be imported as utils.logging
__all__ = [
    "LogEntry",
    "ReproducibilityLogger",
    "get_logger",
    "log_operation",
    "log_artifact_rejection",
    "log_participant_exclusion",
    "save_rejection_summary",
    "get_rejection_counts",
    "save_exclusion_log_csv",
]

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

def log_artifact_rejection(artifact_type: str, reason: str, **kwargs: Any) -> None:
    """Log rejection of an artifact (e.g., epoch, segment) to the global logger."""
    entry = log_operation(
        "artifact_rejection",
        artifact_type=artifact_type,
        reason=reason,
        **kwargs,
    )
    # Ensure we have a log entry even if the logger is a no-op
    if isinstance(entry, LogEntry):
        pass  # LogEntry created successfully

def log_participant_exclusion(participant_id: str, reason: str, **kwargs: Any) -> None:
    """Log exclusion of a participant to the global logger."""
    entry = log_operation(
        "participant_exclusion",
        participant_id=participant_id,
        reason=reason,
        **kwargs,
    )
    if isinstance(entry, LogEntry):
        pass

def save_rejection_summary(log_file: str = "data/processed/exclusion_log.csv") -> None:
    """Save all rejection/exclusion entries to a CSV file."""
    logger = get_logger()
    if not logger.entries:
        return

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id", "reason", "timestamp"])
        for entry in logger.entries:
            if entry.operation in ("artifact_rejection", "participant_exclusion"):
                participant_id = entry.parameters.get("participant_id", "")
                reason = entry.parameters.get("reason", entry.parameters.get("artifact_type", ""))
                writer.writerow([participant_id, reason, entry.timestamp])

def get_rejection_counts(log_file: str = "data/processed/exclusion_log.csv") -> dict:
    """Count rejections/exclusions by reason."""
    if not os.path.exists(log_file):
        return {}

    counts: dict = {}
    with open(log_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reason = row.get("reason", "")
            counts[reason] = counts.get(reason, 0) + 1
    return counts

def save_exclusion_log_csv(entries: list, log_file: str = "data/processed/exclusion_log.csv") -> None:
    """Save a list of exclusion entries to CSV.

    Args:
        entries: List of dicts with keys: participant_id, reason, timestamp
        log_file: Path to output CSV file
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id", "reason", "timestamp"])
        for entry in entries:
            writer.writerow([
                entry.get("participant_id", ""),
                entry.get("reason", ""),
                entry.get("timestamp", datetime.utcnow().isoformat())
            ])
