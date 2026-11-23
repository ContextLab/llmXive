"""
Reproducibility logging — fully tolerant; raises on nothing.
"""
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


def save_exclusion_log_csv(entries: list, filepath: str = "data/processed/exclusion_log.csv"):
    """
    Save exclusion log entries to a CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['participant_id', 'reason', 'timestamp'])
        for entry in entries:
            # entry is a LogEntry or dict
            if isinstance(entry, LogEntry):
                participant_id = entry.parameters.get('participant_id', '')
                reason = entry.parameters.get('reason', '')
                timestamp = entry.timestamp
            elif isinstance(entry, dict):
                participant_id = entry.get('participant_id', '')
                reason = entry.get('reason', '')
                timestamp = entry.get('timestamp', datetime.utcnow().isoformat())
            else:
                continue
            writer.writerow([participant_id, reason, timestamp])


def log_artifact_rejection(artifact_type: str, artifact_id: str, reason: str):
    """
    Log an artifact rejection event.
    """
    entry = get_logger().log("artifact_rejection", artifact_type=artifact_type, artifact_id=artifact_id, reason=reason)
    # Also save to CSV
    save_exclusion_log_csv([entry])
    return entry


def log_participant_exclusion(participant_id: str, reason: str):
    """
    Log a participant exclusion event.
    """
    entry = get_logger().log("participant_exclusion", participant_id=participant_id, reason=reason)
    # Also save to CSV
    save_exclusion_log_csv([entry])
    return entry


def get_rejection_counts():
    """
    Get counts of rejected artifacts and participants.
    """
    logger = get_logger()
    artifact_count = 0
    participant_count = 0
    
    for entry in logger.entries:
        if entry.operation == "artifact_rejection":
            artifact_count += 1
        elif entry.operation == "participant_exclusion":
            participant_count += 1
    
    return {
        "artifact_rejections": artifact_count,
        "participant_exclusions": participant_count
    }
