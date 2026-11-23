"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialize the log entry as a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A minimal logger that never raises and stores LogEntry objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Create a LogEntry from the given operation name and parameters."""
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # any standard logging method (info, debug, warning, error, critical, etc.)
    # simply becomes a no‑op – the analysis scripts only need the .log() method.
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper.

    * As a decorator: ``@log_operation("my_op")`` wraps the function unchanged.
    * As a direct call: ``log_operation("my_op", key=value)`` returns a LogEntry.
    """
    # Decorator usage – first positional arg is a callable and no explicit kwargs
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call usage – first positional arg is the operation name
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def update_log_section(section: str, payload: dict) -> None:
    """Append a generic ``payload`` dict to a named ``section`` in the global logger.

    The logger stores a flat list of LogEntry objects; this helper simply creates
    a new LogEntry with ``operation`` set to the section name and the payload
    stored under ``parameters``.  All callers treat it as a fire‑and‑forget
    operation, so the implementation is intentionally lightweight.
    """
    get_logger().log(section, **payload)
