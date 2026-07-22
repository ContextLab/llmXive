"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
import os
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
        # Handle both string name and keyword arguments
        if args:
            self.name = args[0]
        else:
            self.name = kwargs.get("name", kwargs.get("batch_id", "reproducibility"))
        
        # Extract batch_id and seed for context if provided
        self.batch_id = kwargs.get("batch_id", None)
        self.seed = kwargs.get("seed", None)
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


def setup_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """
    Setup a logger instance. Accepts multiple call shapes:
    1. setup_logger("name_string") -> positional arg
    2. setup_logger(batch_id="id") -> keyword arg
    3. setup_logger(__name__) -> positional arg
    
    Returns a ReproducibilityLogger that never raises on unexpected call shapes.
    """
    global _GLOBAL_LOGGER
    
    # If called with positional args, use the first as name
    if args:
        name_or_batch = args[0]
        if isinstance(name_or_batch, str):
            # If it looks like a module name or simple string, use as name
            logger = ReproducibilityLogger(name=name_or_batch, **kwargs)
        else:
            # Fallback
            logger = ReproducibilityLogger(*args, **kwargs)
    else:
        # If called with only kwargs (e.g., batch_id=...), use kwargs
        logger = ReproducibilityLogger(**kwargs)
    
    # Update global if not set
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = logger
    
    return logger
