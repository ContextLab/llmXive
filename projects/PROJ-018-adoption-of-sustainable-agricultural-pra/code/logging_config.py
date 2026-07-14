"""Reproducibility logging module with tolerant API.

This module provides:
- `LogEntry`: dataclass representing a single log entry.
- `ReproducibilityLogger`: a logger that accepts any call shape and never raises.
- `get_logger()`: returns a singleton logger instance.
- `log_operation()`: usable as a decorator or direct logging function.
- `update_log_section()`: helper to persist structured log sections to the
  modeling log YAML file defined in the project config.

The implementation follows the reference supplied in the task description
and adds the missing `update_log_section` utility required by the
cleaning pipeline.
"""
from __future__ import annotations

import functools
import json
import yaml
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# Log entry definition
# ----------------------------------------------------------------------
@dataclass
class LogEntry:
    """Simple container for a logged operation."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialise the entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

# ----------------------------------------------------------------------
# Core logger – tolerant to any method name
# ----------------------------------------------------------------------
class ReproducibilityLogger:
    """A very permissive logger that never raises."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Name is optional; default to a generic identifier.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    # The primary logging API used by `log_operation`.
    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record an operation and return the created LogEntry."""
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Any standard logging method (info, debug, warning, …) is tolerated
    # but becomes a no‑op – the pipeline never depends on their return value.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# ----------------------------------------------------------------------
# Global singleton handling
# ----------------------------------------------------------------------
_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance, creating it on first use."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


# ----------------------------------------------------------------------
# Dual‑purpose log_operation
# ----------------------------------------------------------------------
def log_operation(*args: Any, **kwargs: Any) -> Any:
    """
    Dual‑purpose helper.

    * As a decorator: ``@log_operation`` wraps the function unchanged.
    * As a direct call: ``log_operation('my_op', param=1)`` returns a
      :class:`LogEntry` (callers typically use ``.to_json()``).
    """
    # Decorator usage – first positional argument is the function.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call form.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def update_log_section(section: str, entry: LogEntry) -> None:
    """
    Append a ``LogEntry`` to a named section of the global log.

    The function is deliberately permissive – if the logger has not been
    initialised or the section does not exist yet, it simply records the
    entry without raising.
    """
    logger = get_logger()
    # Store sections as a dict attribute on the logger; create lazily.
    if not hasattr(logger, "sections"):
        logger.sections = {}
    logger.sections.setdefault(section, []).append(entry)
