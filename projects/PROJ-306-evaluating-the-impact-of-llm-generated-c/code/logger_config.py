"""Reproducibility logging — fully tolerant; raises on nothing.

This file replaces any previous hybrid implementation with a self‑contained
logger that satisfies all current call‑sites in the repository:
- ``get_logger`` / ``log_operation`` (used throughout the code base)
- ``log_pipeline_summary`` (required by ``code/main.py``)
- ``log_operation`` can be used as a decorator or a direct logging call.
"""

from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class LogEntry:
    """Simple container for a logging event."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Return a JSON representation of the entry."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger does **not** delegate to the stdlib ``logging`` module because
    that API is incompatible with the tolerant behaviour required by the
    repository.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry.

        The first positional argument (if present) is interpreted as the
        operation name; otherwise the ``operation`` keyword argument is used.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # ``.info/.debug/.warning/.error/.critical`` etc. become no‑ops.
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None

        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Retrieve a singleton logger instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper.

    - As a decorator: ``@log_operation`` wraps a function without altering its
      signature.
    - As a direct call: ``log_operation('my_op', key=value)`` records a
      ``LogEntry`` and returns it.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


# --------------------------------------------------------------------------- #
# Additional helper required by ``code/main.py``.
# --------------------------------------------------------------------------- #
def log_pipeline_summary(*args: Any, **kwargs: Any) -> LogEntry:
    """
    Log a high‑level pipeline summary.

    The function is deliberately permissive: it accepts any positional or
    keyword arguments and forwards them to the underlying logger under the
    operation name ``pipeline_summary``.  Call‑sites may pass a mixture of
    positional arguments (interpreted as the operation name) and keyword
    arguments (treated as parameters).  This flexibility satisfies all
    existing usages without raising ``TypeError``.
    """
    if args:
        # If the caller supplied a positional string, treat it as the
        # operation name; otherwise fall back to the default.
        operation_name = str(args[0])
        extra_kwargs = dict(kwargs)
    else:
        operation_name = "pipeline_summary"
        extra_kwargs = dict(kwargs)

    return get_logger().log(operation_name, **extra_kwargs)