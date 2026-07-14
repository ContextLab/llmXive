"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class LogEntry:
    """Simple container for a logged operation."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialise the log entry as JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A very permissive logger that never raises.

    It stores LogEntry objects internally and pretends to have the standard
    logging methods (info, debug, warning, error, critical) as no‑ops.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Accept any positional/keyword arguments – they are ignored.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry.

        The first positional argument (or the ``operation`` keyword) is taken as the
        operation name. All remaining keyword arguments are stored as parameters.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Any standard logging method simply becomes a no‑op that returns None.
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance.

    The first call creates the logger; subsequent calls return the same instance,
    ignoring any additional arguments.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any):
    """Dual‑purpose helper used either as a decorator or as a direct logging call.

    *Decorator usage*:

    >>> @log_operation
    ... def foo(...):
    ...     ...

    The decorator returns the original function unchanged (wrapping it only to keep
    the signature). No log entry is created at decoration time.

    *Direct‑call usage*:

    >>> log_operation("my_op", param1=val)

    Returns a :class:`LogEntry` instance which callers can serialise via
    ``.to_json()``.
    """
    # Decorator form – a single callable positional argument and no kwargs.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any):
            return func(*a, **k)

        return _wrapper

    # Direct‑call form.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
