"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import csv
import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# Constants for exclusion logging
LOGS_DIR = "data/processed"
EXCLUSION_LOG_PATH = os.path.join(LOGS_DIR, "exclusion_log.csv")

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


def log_artifact_rejection(
    artifact_type: str,
    reason: str,
    participant_id: str,
    epoch_indices: list | None = None,
    channel: str | None = None,
    **kwargs: Any,
) -> None:
    """Log artifact rejection to the exclusion log CSV.

    Args:
        artifact_type: Type of artifact (e.g., 'epoch', 'channel')
        reason: Reason for rejection
        participant_id: ID of the participant
        epoch_indices: List of rejected epoch indices
        channel: Channel name if applicable
        **kwargs: Additional parameters
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    entry = {
        "participant_id": participant_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "artifact_type": artifact_type,
        "details": json.dumps({
            "epoch_indices": epoch_indices,
            "channel": channel,
            **kwargs
        }) if (epoch_indices or channel or kwargs) else ""
    }

    # Check if file exists to determine header
    file_exists = os.path.exists(EXCLUSION_LOG_PATH)

    with open(EXCLUSION_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["participant_id", "reason", "timestamp", "artifact_type", "details"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)


def log_participant_exclusion(
    participant_id: str,
    reason: str,
    **kwargs: Any,
) -> None:
    """Log participant exclusion to the exclusion log CSV.

    Args:
        participant_id: ID of the excluded participant
        reason: Reason for exclusion
        **kwargs: Additional parameters
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    entry = {
        "participant_id": participant_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "artifact_type": "participant",
        "details": json.dumps(kwargs) if kwargs else ""
    }

    # Check if file exists to determine header
    file_exists = os.path.exists(EXCLUSION_LOG_PATH)

    with open(EXCLUSION_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["participant_id", "reason", "timestamp", "artifact_type", "details"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)


def save_rejection_summary(rejections: list, output_path: str = None) -> None:
    """Save a summary of rejections to a file.

    Args:
        rejections: List of rejection entries
        output_path: Output file path (defaults to exclusion log path)
    """
    if output_path is None:
        output_path = EXCLUSION_LOG_PATH

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="") as f:
        if rejections:
            writer = csv.DictWriter(f, fieldnames=rejections[0].keys())
            writer.writeheader()
            writer.writerows(rejections)


def get_rejection_counts() -> dict:
    """Get counts of rejections by reason.

    Returns:
        Dictionary mapping reason to count
    """
    if not os.path.exists(EXCLUSION_LOG_PATH):
        return {}

    counts = {}
    with open(EXCLUSION_LOG_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reason = row.get("reason", "unknown")
            counts[reason] = counts.get(reason, 0) + 1

    return counts


def save_exclusion_log_csv(entries: list, log_file: str = None) -> None:
    """Save exclusion log entries to CSV.

    Args:
        entries: List of exclusion entries (dicts)
        log_file: Output file path (defaults to EXCLUSION_LOG_PATH)
    """
    if log_file is None:
        log_file = EXCLUSION_LOG_PATH

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    if not entries:
        return

    # Determine fieldnames from first entry
    fieldnames = list(entries[0].keys())

    with open(log_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
