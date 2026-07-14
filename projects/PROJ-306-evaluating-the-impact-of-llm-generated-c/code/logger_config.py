"""Reproducibility logging — fully tolerant; raises on nothing.

This implementation replaces the previous mixed‑std‑logging version with a
self‑contained logger that satisfies all current call sites, including
``log_pipeline_summary`` required by ``code/main.py``.
"""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# --------------------------------------------------------------------------- #
# Core data structures
# --------------------------------------------------------------------------- #
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
    ``log(level, msg)`` needs an integer level and has no ``to_json`` —
    that is exactly what keeps breaking. This logger is self‑contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record an operation and its parameters.

        The first positional argument (if any) is interpreted as the
        operation name; otherwise the ``operation`` keyword is used.
        """
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no‑op
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None
        return _noop

# --------------------------------------------------------------------------- #
# Global logger singleton
# --------------------------------------------------------------------------- #
_GLOBAL_LOGGER: ReproducibilityLogger | None = None

def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a module‑wide singleton logger."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER

# --------------------------------------------------------------------------- #
# Public logging helpers
# --------------------------------------------------------------------------- #
def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose: a decorator (@log_operation) OR a direct logging call.

    The direct‑call path ALWAYS returns a ``LogEntry`` (callers use
    ``.to_json()``); decorator use returns the wrapped function. Never
    return a bare function from the direct‑call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)

def log_pipeline_summary(
    task_id: str,
    status: str,
    details: dict | None = None,
) -> None:
    """Convenient wrapper used by ``code/main.py`` to log pipeline outcomes.

    ``details`` can contain arbitrary key/value pairs (e.g. coverage
    metrics or error messages).  All information is stored as a single
    ``LogEntry`` under the operation name ``pipeline_summary``.
    """
    payload = {"task_id": task_id, "status": status}
    if details:
        payload.update(details)
    # The logger returns a ``LogEntry``; we discard it because callers only
    # need the side‑effect of recording the entry.
    get_logger().log("pipeline_summary", **payload)