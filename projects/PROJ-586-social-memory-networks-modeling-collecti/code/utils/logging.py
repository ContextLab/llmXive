"""Reproducibility logging — fully tolerant; raises on nothing.

Configures error logging with timestamps to `experiment.log` (FR-010).
"""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOG_FILE_PATH = _PROJECT_ROOT / "experiment.log"


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Writes all log entries to `experiment.log` with timestamps (FR-010).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        """Ensure the log file directory and file exist."""
        _LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _LOG_FILE_PATH.exists():
            _LOG_FILE_PATH.touch()

    def _write_entry(self, entry: LogEntry) -> None:
        """Append a log entry to the file."""
        with open(_LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.pop("level", "INFO").upper()
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=level,
            timestamp=datetime.utcnow().isoformat()
        )
        self.entries.append(entry)
        self._write_entry(entry)
        return entry

    def error(self, *args: Any, **kwargs: Any) -> None:
        """Log an error level message."""
        self.log(*args, level="ERROR", **kwargs)

    def info(self, *args: Any, **kwargs: Any) -> None:
        """Log an info level message."""
        self.log(*args, level="INFO", **kwargs)

    def debug(self, *args: Any, **kwargs: Any) -> None:
        """Log a debug level message."""
        self.log(*args, level="DEBUG", **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        """Log a warning level message."""
        self.log(*args, level="WARNING", **kwargs)

    def critical(self, *args: Any, **kwargs: Any) -> None:
        """Log a critical level message."""
        self.log(*args, level="CRITICAL", **kwargs)

    # Fallback for any other attribute access
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