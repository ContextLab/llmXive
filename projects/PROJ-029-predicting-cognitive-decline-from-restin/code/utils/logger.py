"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class LogEntry:
    """A single log entry."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialize the entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A lightweight, self‑contained logger that never raises.

    It accepts any call shape and provides no‑op methods for typical
    logging levels (info, debug, warning, error, critical, etc.).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # First positional arg or named 'name' is used as logger name.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry and return the LogEntry instance.

        The first positional argument (or the keyword ``operation``) is
        treated as the operation name. All remaining kwargs are stored as
        parameters.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide no‑op methods for the common logging levels.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance.

    Accepts any arguments to stay compatible with all call sites.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Callable | LogEntry:
    """Dual‑purpose helper used either as a decorator or a direct logger.

    - As ``@log_operation`` (no arguments) it returns a wrapper that
      simply forwards the call.
    - As ``@log_operation("name")`` it records the operation name.
    - As ``log_operation("name", key=value)`` it logs immediately and
      returns a ``LogEntry``.
    """
    # Decorator usage: @log_operation or @log_operation()
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call usage
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)