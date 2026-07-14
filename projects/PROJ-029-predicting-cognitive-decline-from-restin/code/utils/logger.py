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
        """Return a JSON representation of the log entry."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A tolerant logger that never raises for unexpected calls.

    It implements the usual logging methods (info, warning, error, etc.)
    as no‑ops and provides a generic ``log`` method that records a
    :class:`LogEntry`.  This design avoids the incompatibilities of the
    standard ``logging.Logger`` which expects integer levels.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ``name`` is optional – we keep it for potential debugging.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry.

        The first positional argument (or the ``operation`` keyword) is used
        as the operation name.  All remaining keyword arguments are stored
        as ``parameters``.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide tolerant no‑op methods for common logging levels.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton ``ReproducibilityLogger``.

    The first argument (or ``name=`` kwarg) can be used to label the logger,
    but subsequent calls return the same instance to keep a unified log.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper usable as a decorator or a direct logging call.

    Supported usage patterns:

    1. ``@log_operation`` – no arguments, simply decorates the function.
    2. ``@log_operation("my_op")`` – decorates and logs the operation name
       each time the function is called.
    3. ``log_operation("my_op", key=value)`` – logs a single entry and
       returns the :class:`LogEntry`.
    """
    # Case 1: used as ``@log_operation`` without parentheses.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Case 2: used as ``@log_operation("name")`` – first arg is a string.
    if len(args) == 1 and isinstance(args[0], str) and not kwargs:
        operation_name = args[0]

        def decorator(func):
            @functools.wraps(func)
            def _wrapper(*a: Any, **k: Any) -> Any:
                # Log the call (arguments are recorded for traceability).
                get_logger().log(operation_name, args=a, kwargs=k)
                return func(*a, **k)

            return _wrapper

        return decorator

    # Case 3: direct call – log and return a LogEntry.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
