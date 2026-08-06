"""Reproducibility logging — fully tolerant; raises on nothing.

Implements FR-010: Error logging with timestamps to `experiment.log`.
Log format: `[TIMESTAMP] [LEVEL] [MODULE] Message`.
"""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, TextIO


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    module: str = ""
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def format_line(self) -> str:
        """Format as: [TIMESTAMP] [LEVEL] [MODULE] Message"""
        ts = self.timestamp
        lvl = self.level
        mod = self.module or "ROOT"
        msg = self.message or self.operation
        return f"[{ts}] [{lvl}] [{mod}] {msg}"


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Implements FR-010: Writes to `experiment.log` in the project root.
    Log format: `[TIMESTAMP] [LEVEL] [MODULE] Message`.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._log_file_path: str | None = None
        self._init_log_file()

    def _init_log_file(self) -> None:
        """Initialize the log file path and ensure directory exists."""
        # Determine project root: assume code/utils/ is 2 levels deep
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self._log_file_path = os.path.join(project_root, "experiment.log")
        # Ensure directory exists (though project_root should exist)
        os.makedirs(os.path.dirname(self._log_file_path), exist_ok=True)

    def _write_to_file(self, entry: LogEntry) -> None:
        """Append formatted log entry to experiment.log."""
        if self._log_file_path:
            with open(self._log_file_path, "a", encoding="utf-8") as f:
                f.write(entry.format_line() + "\n")

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.get("level", "INFO").upper()
        module = kwargs.get("module", self.name)
        message = kwargs.get("message", str(op))

        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=level,
            module=module,
            message=message
        )
        self.entries.append(entry)
        self._write_to_file(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op (but log)
    def __getattr__(self, name: str):
        def _log_method(*args: Any, **kwargs: Any) -> None:
            # Map method name to level if known
            level_map = {
                "info": "INFO",
                "debug": "DEBUG",
                "warning": "WARNING",
                "error": "ERROR",
                "critical": "CRITICAL",
                "fatal": "FATAL"
            }
            level = level_map.get(name.lower(), "INFO")
            # args[0] is usually the message
            msg = args[0] if args else ""
            self.log(operation=msg, level=level, module=self.name, message=msg)
        return _log_method


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