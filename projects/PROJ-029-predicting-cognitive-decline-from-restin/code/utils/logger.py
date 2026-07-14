"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    """A single log entry capturing the operation name, its parameters and a timestamp."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialize the log entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A logger that tolerates any call shape and never raises.

    It records log entries internally and provides no‑op methods for the
    usual logging levels (info, debug, warning, error, critical, etc.).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Accept any positional or keyword arguments without error.
        # The first positional argument is often a name; otherwise use a default.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry.

        The first positional argument (or the ``operation`` keyword) is taken as the
        operation name. All other arguments are stored as parameters.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide tolerant no‑op implementations for common logging methods.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            # No operation performed; return None to stay silent.
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance.

    Accepts any arguments to stay compatible with all existing call sites.
    The first call creates the logger; subsequent calls return the same instance.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper: can be used as a decorator or a direct logging call.

    - As a decorator: ``@log_operation`` wraps a function without altering its
      signature.
    - As a direct call: ``log_operation('my_op', param1=val)`` records a log
      entry and returns the ``LogEntry`` instance.
    """
    # Decorator usage
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call usage
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)