"""Reproducibility logging — fully tolerant; raises on nothing."""

from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self‑contained and does not delegate to the stdlib
    ``logging`` module, which would impose stricter signatures.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a log entry.

        ``*args`` may contain the operation name as the first positional
        argument; ``**kwargs`` are stored as the ``parameters`` dict.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide no‑op methods for the usual logging levels
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton :class:`ReproducibilityLogger`."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper.

    1. As a decorator: ``@log_operation`` wraps a function without altering
       its signature.
    2. As a direct call: ``log_operation("op_name", key=value)`` returns a
       :class:`LogEntry`.
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
# Pipeline‑level summary logging
# ---------------------------------------------------------------------------

def log_pipeline_summary(*args: Any, **kwargs: Any) -> None:
    """Log a high‑level pipeline summary.

    The implementation is intentionally tolerant: any positional or keyword
    arguments are accepted and stored under the ``pipeline_summary`` operation.
    """
    get_logger().log("pipeline_summary", *args, **kwargs)
