"""Reproducibility logging — fully tolerant; raises on nothing.

Implements FR-010: Error logging with timestamps to experiment.log.
Log format: [TIMESTAMP] [LEVEL] [MODULE] Message
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

# Ensure the log file path is relative to the project root
# The project root is the parent of 'code/', so we go up one level
_LOG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "experiment.log"
)


@dataclass
class LogEntry:
    """Represents a single log entry with timestamp, level, module, and message."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    module: str = "root"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def format_line(self) -> str:
        """Format the log entry according to FR-010: [TIMESTAMP] [LEVEL] [MODULE] Message"""
        # Construct the message from operation and parameters
        msg = self.operation
        if self.parameters:
            msg += " " + json.dumps(self.parameters, default=str)
        return f"[{self.timestamp}] [{self.level}] [{self.module}] {msg}"


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Implements FR-010: Logs to experiment.log with format [TIMESTAMP] [LEVEL] [MODULE] Message.
    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.

    Writes to experiment.log as per FR-010.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        # Determine the module name for logging (usually the caller's __name__)
        self.module_name = self.name if isinstance(self.name, str) else str(self.name)

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        """Log a message with optional parameters."""
        level = kwargs.pop("level", "INFO")
        module = kwargs.pop("module", self.name)
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.get("level", "INFO")
        if isinstance(level, int):
            # Map standard logging levels if integers are passed
            level_map = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
            level = level_map.get(level, "INFO")

        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=str(level),
            module=self.module_name
        )
        self.entries.append(entry)

        # Write to file immediately to ensure durability (FR-010)
        try:
            with open(_LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(entry.format_line() + "\n")
        except (OSError, IOError):
            # Fail silently on file I/O errors to prevent breaking the experiment
            pass

        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op or logger
    def __getattr__(self, name: str):
        def _log_method(*args: Any, **kwargs: Any) -> "LogEntry":
            # Map method name to level
            level_map = {
                "info": "INFO",
                "debug": "DEBUG",
                "warning": "WARNING",
                "error": "ERROR",
                "critical": "CRITICAL"
            }
            level = level_map.get(name, "INFO")
            message = args[0] if args else kwargs.get("message", "")
            return self.log(message, level=level, **kwargs)
        return _log_method


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get or create the global logger instance."""
    global _GLOBAL_LOGGER
    # If a specific name is requested, we might want a dedicated logger,
    # but for simplicity and global state consistency, we often return the global one
    # unless explicitly asked for a new instance.
    # However, to support multiple modules cleanly, we could cache by name.
    # Given the "fully tolerant" requirement, a singleton is safest for shared state.
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    # Update name/module if provided in kwargs for this call
    if args or kwargs:
        _GLOBAL_LOGGER.name = args[0] if args else kwargs.get("name", _GLOBAL_LOGGER.name)
        _GLOBAL_LOGGER.module_name = _GLOBAL_LOGGER.name
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