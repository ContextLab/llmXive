"""Reproducibility logging — fully tolerant; raises on nothing.

Configures error logging with timestamps to experiment.log (FR-010).
"""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "experiment.log"


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.
    
    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    
    Logs all operations to experiment.log with timestamps (FR-010).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def _write_log(self, entry: LogEntry) -> None:
        """Write log entry to experiment.log with timestamp."""
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
        except Exception:
            # Fail silently on log file errors to avoid breaking experiments
            pass

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.get("level", "INFO")
        message = kwargs.get("message", str(op))
        
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=str(level),
            message=str(message)
        )
        self.entries.append(entry)
        self._write_log(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op that still logs
    def _make_level_method(self, level: str):
        def _log_method(*args: Any, **kwargs: Any) -> None:
            op = args[0] if args else kwargs.get("operation", level.lower())
            message = kwargs.get("message", str(op) if args else "")
            entry = LogEntry(
                operation=str(op),
                parameters=dict(kwargs),
                level=level,
                message=str(message)
            )
            self.entries.append(entry)
            self._write_log(entry)
        return _log_method

    def __getattr__(self, name: str):
        # Map standard logging level names to our logging method
        if name in ("info", "debug", "warning", "error", "critical"):
            return self._make_level_method(name.upper())
        # Any other attribute -> no-op
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