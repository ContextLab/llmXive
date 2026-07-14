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
        """Serialise the entry as JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A logger that tolerates any call shape and never raises.

    It deliberately does **not** delegate to the stdlib ``logging`` module,
    because that API is strict about argument types (e.g. ``log(level,
    msg)`` expects an integer level).  All methods simply accept ``*args``
    and ``**kwargs`` and either record a ``LogEntry`` (for ``log``) or act
    as a no‑op (for ``info``, ``debug``, ``warning``, etc.).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a generic log entry.

        The first positional argument (if any) is interpreted as the operation
        name; any keyword arguments become the ``parameters`` mapping.
        """
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Any standard logging method (info, debug, warning, error, critical, etc.)
    # simply returns a no‑op function that discards its arguments.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton ``ReproducibilityLogger``.

    The first positional argument or the ``name`` keyword is used as the
    logger's identifier.  Subsequent calls return the same instance,
    regardless of the arguments supplied.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper that works as a decorator *or* a direct logger.

    - As a decorator: ``@log_operation`` wraps a function and returns it
      unchanged.
    - As a direct call: ``log_operation('my_op', key=value)`` records a
      ``LogEntry`` via the global logger and returns that entry.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)