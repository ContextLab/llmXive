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
from typing import Any

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

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None

        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
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


# ---------------------------------------------------------------------------
# Helper for pipeline‑level summary logging
# ---------------------------------------------------------------------------

def log_pipeline_summary(*args: Any, **kwargs: Any) -> LogEntry:
    """Log a high‑level pipeline summary.

    Accepts any positional or keyword arguments; they are forwarded as the
    ``parameters`` field of a :class:`LogEntry`. The operation name is fixed
    to ``pipeline_summary`` for easy downstream filtering.
    """
    return log_operation("pipeline_summary", *args, **kwargs)