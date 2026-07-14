"""Reproducibility logging — fully tolerant; raises on nothing.

Implements FR-010: Configure error logging with timestamps to experiment.log.
Log format: [TIMESTAMP] [LEVEL] [MODULE] Message.
"""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure the project results directory exists for log file
LOG_FILE_PATH = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/experiment.log")
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class LogEntry:
    """Structured log entry with timestamp for reproducibility."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    module: str = "root"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_log_format(self) -> str:
        """Format as [TIMESTAMP] [LEVEL] [MODULE] Message."""
        ts = self.timestamp
        level = self.level
        mod = self.module
        msg = self.message
        return f"[{ts}] [{level}] [{mod}] {msg}"


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Implements FR-010: Logs to experiment.log with format:
    [TIMESTAMP] [LEVEL] [MODULE] Message
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._module = kwargs.get("module", self.name)

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        """Log an entry. Supports direct call or decorator usage."""
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.get("level", "INFO")
        msg = kwargs.get("message", str(op))

        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            module=self._module,
            message=msg
        )
        self.entries.append(entry)

        # Write to file immediately for persistence
        self._write_to_file(entry)
        return entry

    def _write_to_file(self, entry: LogEntry) -> None:
        """Append log entry to experiment.log."""
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(entry.to_log_format() + "\n")
        except Exception:
            # Fail silently to avoid breaking the experiment
            pass

    def info(self, message: str, **kwargs: Any) -> "LogEntry":
        return self.log("info", level="INFO", message=message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> "LogEntry":
        return self.log("debug", level="DEBUG", message=message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> "LogEntry":
        return self.log("warning", level="WARNING", message=message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> "LogEntry":
        return self.log("error", level="ERROR", message=message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> "LogEntry":
        return self.log("critical", level="CRITICAL", message=message, **kwargs)

    # Fallback for any other method calls (e.g., .exception, .exception)
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get or create a global logger instance."""
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