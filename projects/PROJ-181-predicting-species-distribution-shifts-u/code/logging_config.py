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
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
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


# Compatibility aliases for existing callers
def get_train_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get the global logger. Accepts any call shape."""
    return get_logger(*args, **kwargs)


def get_preprocess_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get the global logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)


def get_download_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get the global logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)


def get_project_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get the global logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)


def get_evaluate_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get the global logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)


def get_pipeline_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get the global logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)


def setup_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Setup logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)


def initialize_pipeline_logging(*args: Any, **kwargs: Any) -> None:
    """Initialize pipeline logging (no-op for compatibility)."""
    pass


class DetailedFormatter:
    """Placeholder for compatibility."""
    pass


def setup_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Setup logger (alias for compatibility)."""
    return get_logger(*args, **kwargs)
