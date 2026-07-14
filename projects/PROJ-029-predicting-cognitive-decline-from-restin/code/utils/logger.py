"""
Reproducibility logging utilities.
Provides a tolerant logger and a flexible @log_operation decorator
that can be used both as a decorator (with or without an explicit
operation name) and as a direct logging call.
"""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, List


@dataclass
class LogEntry:
    """Simple container for a logging event."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialize the log entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """
    Minimal logger that never raises regardless of how it is called.

    It stores LogEntry objects internally and provides no‑op methods for
    the usual logging levels (info, debug, warning, error, etc.).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Accept any positional or keyword arguments for maximum tolerance.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: List[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """
        Record a log entry.

        The first positional argument (or the ``operation`` keyword) is taken
        as the operation name.  All other keyword arguments are stored as
        parameters.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide tolerant no‑op implementations for common logging methods.
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """
    Return a singleton ``ReproducibilityLogger``.

    The function accepts any arguments so callers can pass a name or other
    parameters without causing errors.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """
    Dual‑purpose decorator / logging helper.

    Usage patterns supported:

    1. ``@log_operation`` – decorates a function; the function name is used
       as the operation name when the wrapper is invoked.
    2. ``@log_operation("custom_name")`` – decorates a function; the
       supplied string is used as the operation name.
    3. ``log_operation("op_name", key=value)`` – direct call that returns a
       ``LogEntry``.

    The decorator variant logs the operation *once* each time the wrapped
    function is called, then forwards all arguments to the original
    function.  The direct‑call variant simply records a log entry and
    returns it.
    """
    # --------------------------------------------------------------
    # Decorator without arguments: @log_operation
    # --------------------------------------------------------------
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func: Callable = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            # Log using the function's __name__ as the operation.
            get_logger().log(func.__name__)
            return func(*a, **k)

        return _wrapper

    # --------------------------------------------------------------
    # Decorator with a single string argument: @log_operation("name")
    # --------------------------------------------------------------
    if len(args) == 1 and isinstance(args[0], str) and not kwargs:
        operation_name: str = args[0]

        def _decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def _wrapper(*a: Any, **k: Any) -> Any:
                get_logger().log(operation_name)
                return func(*a, **k)
            return _wrapper

        return _decorator

    # --------------------------------------------------------------
    # Direct‑call usage: log_operation("op_name", key=value)
    # --------------------------------------------------------------
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)