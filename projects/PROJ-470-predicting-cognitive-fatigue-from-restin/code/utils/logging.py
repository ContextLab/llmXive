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
        self.log_file = kwargs.get("log_file", None)
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        if self.log_file:
            self._write_to_file(entry)
        return entry

    def _write_to_file(self, entry: LogEntry) -> None:
        if not self.log_file:
            return
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        file_exists = os.path.exists(self.log_file)
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['operation', 'parameters', 'timestamp'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'operation': entry.operation,
                'parameters': json.dumps(entry.parameters),
                'timestamp': entry.timestamp
            })

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


def log_artifact_rejection(artifact_id: str, reason: str) -> None:
    """Log rejection of an artifact."""
    logger = get_logger("artifact_rejection")
    logger.log("artifact_rejected", artifact_id=artifact_id, reason=reason)


def log_participant_exclusion(participant_id: str, reason: str) -> None:
    """Log exclusion of a participant."""
    logger = get_logger("participant_exclusion")
    logger.log("participant_excluded", participant_id=participant_id, reason=reason)


def save_rejection_summary(output_path: str) -> None:
    """Save a summary of rejections to a CSV file."""
    logger = get_logger("rejection_summary")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['operation', 'parameters', 'timestamp'])
        writer.writeheader()
        for entry in logger.entries:
            writer.writerow({
                'operation': entry.operation,
                'parameters': json.dumps(entry.parameters),
                'timestamp': entry.timestamp
            })


def get_rejection_counts() -> dict:
    """Get counts of different rejection types."""
    logger = get_logger("rejection_summary")
    counts = {}
    for entry in logger.entries:
        op = entry.operation
        counts[op] = counts.get(op, 0) + 1
    return counts


def save_exclusion_log_csv(exclusions: list, output_path: str) -> None:
    """Save exclusion log to CSV.

    Args:
        exclusions: List of dicts with 'participant_id', 'reason', 'timestamp'
        output_path: Path to write CSV
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not exclusions:
        # Write empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['participant_id', 'reason', 'timestamp'])
            writer.writeheader()
        return

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['participant_id', 'reason', 'timestamp'])
        writer.writeheader()
        for exc in exclusions:
            writer.writerow(exc)
