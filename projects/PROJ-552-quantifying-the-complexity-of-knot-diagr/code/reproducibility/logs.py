"""Reproducibility logging utilities.

Provides a very lightweight logger that writes JSON‑line entries to a
``logs.json`` file under the project ``data/`` directory.  The logger
implements a ``log`` method used throughout the code base.

The original implementation only accepted a parameter‑less
``get_logger`` which caused many modules to fail when they called
``get_logger(__name__)``.  This file now defines ``get_logger`` that
accepts any positional/keyword arguments (they are ignored) and returns a
singleton ``ReproducibilityLogger`` instance.

The ``log_operation`` decorator is also rewritten as a proper decorator
factory that can be used with the ``@log_operation("name",
output_path_arg="path")`` signature used throughout the project.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional

__all__ = [
    "LogEntry",
    "ReproducibilityLogger",
    "get_logger",
    "log_operation",
]


@dataclass
class LogEntry:
    timestamp: float
    operation: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)


class ReproducibilityLogger:
    """Simple JSON‑line logger.

    All entries are appended to ``data/logs.json``.  The directory is
    created on first use.
    """

    _instance: Optional["ReproducibilityLogger"] = None
    _log_path: Path = Path("data/logs.json")

    def __new__(cls) -> "ReproducibilityLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Ensure the log file exists.
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._log_path.exists():
            self._log_path.touch()

    def log(self, operation: str, status: str = "SUCCESS", **details: Any) -> None:
        """Append a log entry."""
        entry = LogEntry(
            timestamp=time.time(),
            operation=operation,
            status=status,
            details=details,
        )
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    # Compatibility shim used by older code that expected ``info``.
    def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        self.log(*args, **kwargs)


def get_logger(*_args: Any, **_kwargs: Any) -> ReproducibilityLogger:
    """Return the singleton logger.

    The function accepts arbitrary positional and keyword arguments so that
    existing calls such as ``get_logger(__name__)`` continue to work.
    """
    return ReproducibilityLogger()


def _safe_log(operation: str, status: str = "SUCCESS", **details: Any) -> None:
    """Best-effort log entry; logging must never break a real computation."""
    try:
        get_logger().log(operation, status=status, **details)
    except Exception:  # pragma: no cover - logging is auxiliary
        pass


def _op_name(args: tuple, kwargs: dict) -> str:
    """Derive an operation name from whatever the caller passed."""
    for a in args:
        if isinstance(a, str):
            return a
    for key in ("operation_name", "operation", "name"):
        v = kwargs.get(key)
        if isinstance(v, str):
            return v
    return "operation"


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Polymorphic operation logger — used three incompatible ways across this
    codebase, so it must tolerate ALL of them and NEVER raise (a logging
    utility must not crash the real analysis):

    1. **bare decorator** ``@log_operation`` — wraps the function, logging each call;
    2. **decorator factory** ``@log_operation("name", output_path_arg="p")`` /
       ``@log_operation(operation_name=..., output_path_arg=...)`` — returns a decorator;
    3. **direct call** ``log_operation("op", in, out, params, status)`` /
       ``log_operation(operation="op", logger=lg)`` / ``log_operation(lg, "op", {...})``
       — logs immediately; the return value is ignored by such callers.

    Logging is best-effort/auxiliary; the wrapped function's real work and
    outputs are always preserved.
    """
    import functools

    def _wrap(func: Callable, name: str) -> Callable:
        @functools.wraps(func)
        def wrapper(*a: Any, **k: Any) -> Any:
            result = func(*a, **k)
            _safe_log(name, status="SUCCESS")
            return result
        return wrapper

    # (1) bare decorator: a single callable positional, no keywords.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        return _wrap(func, getattr(func, "__name__", "operation"))

    # (3) direct-call side effect (harmless for the factory form too).
    _safe_log(_op_name(args, kwargs), status=str(kwargs.get("status", "SUCCESS")))

    # (2) decorator factory: return a decorator so @log_operation(...) works;
    # direct callers simply ignore this return value.
    def decorator(func: Callable) -> Callable:
        return _wrap(func, _op_name(args, kwargs) if (args or kwargs) else getattr(func, "__name__", "operation"))

    return decorator
