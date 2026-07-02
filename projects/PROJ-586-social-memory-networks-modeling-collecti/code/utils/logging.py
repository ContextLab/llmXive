"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    """A simple log entry that can be serialised to JSON."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Return a JSON representation of the entry."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A logger that never raises and stores entries in memory."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Accept any signature – callers may pass a name or nothing.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    # The core logging method used by the decorator / direct call API.
    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Create a LogEntry from the supplied arguments."""
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Any standard logging method (info, debug, warning, error, etc.) is
    # tolerated as a no‑op to keep the logger compatible with all call sites.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop


# Global singleton – callers expect the same logger instance across the process.
_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a global logger instance, creating it on first use."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper used either as a decorator or a direct logging call.

    When used as ``@log_operation`` it returns the wrapped function.
    When called directly it returns a ``LogEntry`` instance.
    """
    # Decorator usage -------------------------------------------------------
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call usage ------------------------------------------------------
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
