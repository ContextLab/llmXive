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
    """A single reproducibility log entry."""

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
    """A logger that never raises regardless of how it is called."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Name is optional; default to a generic identifier.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    # The primary logging API used by `log_operation`.
    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Create a LogEntry and store it."""
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Accept any conventional logging method (info, debug, warning, error, etc.)
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
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
    """Can be used as a decorator or as a direct logging call.

    *Decorator usage*:
        @log_operation
        def func(...):
            ...

    *Direct call*:
        log_operation("some_name", key=value)

    The direct‑call form always returns a ``LogEntry`` instance.
    """
    # Decorator form – a single callable positional argument and no kwargs.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call form.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


# ----------------------------------------------------------------------
# Helper to persist structured sections to the modelling log file
# ----------------------------------------------------------------------
def update_log_section(section_key: str, data: dict) -> None:
    """Update ``section_key`` in the modelling log YAML file.

    The modelling log path is obtained via ``config.get_modeling_log_path()``.
    If the file does not exist, it is created. Existing sections are
    overwritten with the provided ``data`` dictionary.

    Args:
        section_key: Top‑level key under which to store ``data``.
        data: Dictionary (or JSON‑serialisable mapping) to persist.
    """
    # Import here to avoid circular imports at module load time.
    from config import get_modeling_log_path

    log_path: Path = get_modeling_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing content if present.
    if log_path.is_file():
        try:
            with log_path.open("r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    else:
        existing = {}

    # Update the specific section.
    existing[section_key] = data

    # Write back safely.
    with log_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(existing, f, sort_keys=False)

# ----------------------------------------------------------------------
# End of module
# ----------------------------------------------------------------------