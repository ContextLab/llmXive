"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    """A single log entry describing an operation."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialise the log entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A lightweight logger that never raises for unexpected calls.

    It stores LogEntry objects internally and provides no‑op methods for
    typical logging levels (info, debug, warning, error, critical).  This
    implementation is deliberately independent of the stdlib ``logging``
    module to satisfy the heterogeneous call‑sites across the project.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ``name`` is optional; default to a generic identifier.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry.

        The first positional argument, if present, is interpreted as the
        operation name; otherwise the ``operation`` keyword argument is used.
        All remaining keyword arguments are stored as ``parameters``.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide tolerant no‑op methods for common logging levels.
    def __getattr__(self, name: str):
        def _noop(*_a: Any, **_k: Any) -> None:
            return None

        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance.

    All callers receive the same logger object, satisfying the requirement
    that multiple modules share a common logging store.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper: can be used as a decorator or a direct logger.

    - As a decorator: ``@log_operation`` wraps the target function unchanged.
    - As a function call: ``log_operation('my_op', key=val)`` records a
      LogEntry via the global logger and returns that entry.
    """
    # Decorator usage detection.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call usage.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
