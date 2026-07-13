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
from typing import Any, Optional

# Project root for log file placement (relative to project root)
_LOG_FILE_PATH = "projects/PROJ-586-social-memory-networks-modeling-collecti/experiment.log"


@dataclass
class LogEntry:
    """Represents a single log entry with timestamp, level, module, and message."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    module: str = "root"
    message: str = ""
    parameters: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_log_format(self) -> str:
        """Format as [TIMESTAMP] [LEVEL] [MODULE] Message."""
        return f"[{self.timestamp}] [{self.level}] [{self.module}] {self.message}"


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Implements FR-010: Logs to experiment.log with format [TIMESTAMP] [LEVEL] [MODULE] Message.
    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._log_file_path = kwargs.get("log_file_path", _LOG_FILE_PATH)
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Ensure the directory for the log file exists."""
        log_path = os.path.abspath(self._log_file_path)
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def _write_to_file(self, entry: LogEntry) -> None:
        """Append log entry to experiment.log."""
        log_path = os.path.abspath(self._log_file_path)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry.to_log_format() + "\n")

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        """Log a message with optional parameters."""
        level = kwargs.pop("level", "INFO")
        module = kwargs.pop("module", self.name)
        op = args[0] if args else kwargs.get("operation", "")
        message = kwargs.pop("message", str(op) if op else "")

        entry = LogEntry(
            level=str(level),
            module=str(module),
            message=str(message),
            parameters=dict(kwargs)
        )
        self.entries.append(entry)
        self._write_to_file(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op with logging
    def __getattr__(self, name: str):
        def _log_method(*args: Any, **kwargs: Any) -> None:
            level_map = {
                "info": "INFO",
                "debug": "DEBUG",
                "warning": "WARNING",
                "error": "ERROR",
                "critical": "CRITICAL"
            }
            level = level_map.get(name.lower(), "INFO")
            message = args[0] if args else kwargs.get("message", "")
            self.log(level=level, module=self.name, message=message, **kwargs)
        return _log_method


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get or create the global logger instance."""
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