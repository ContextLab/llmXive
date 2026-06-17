"""Reproducibility logging utilities (robust, tolerant).

This module is imported and called inconsistently across the analysis scripts
(``logger.log('x','y')``, ``logger.debug(a, b)``, ``get_logger(__name__)``,
``log_operation`` as a bare decorator / a decorator factory / a direct call in
several signatures). Logging is AUXILIARY — it must never crash the real
analysis — so every public method here accepts ``*args, **kwargs`` and is
best-effort: it writes a JSON-line entry to ``data/logs.json`` when it can and
silently no-ops on any logging-internal error. The scripts' real computations
and outputs are unaffected.
"""
from __future__ import annotations

import json
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


def _coerce_op(args: tuple, kwargs: dict) -> str:
    for a in args:
        if isinstance(a, str):
            return a
    for key in ("operation", "operation_name", "name", "message", "msg"):
        v = kwargs.get(key)
        if isinstance(v, str):
            return v
    return "operation"


class ReproducibilityLogger:
    """Singleton JSON-line logger. Every method is tolerant and never raises."""

    _instance: Optional["ReproducibilityLogger"] = None
    _log_path: Path = Path("data/logs.json")

    def __new__(cls, *args: Any, **kwargs: Any) -> "ReproducibilityLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self._log_path.exists():
                self._log_path.touch()
        except Exception:
            pass

    def _write(self, operation: str, status: str, details: Dict[str, Any]) -> None:
        try:
            entry = LogEntry(time.time(), str(operation), str(status), dict(details))
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), default=str) + "\n")
        except Exception:  # logging must never break the real computation
            pass

    def log(self, *args: Any, **kwargs: Any) -> None:
        """Flexible: ``log(op)``, ``log(op, status)``, ``log(level, message)``,
        ``log(operation=..., status=..., **d)``, ``log(logger, op, {...})`` etc."""
        op = _coerce_op(args, kwargs)
        str_args = [a for a in args if isinstance(a, str)]
        status = kwargs.get("status") or (str_args[1] if len(str_args) > 1 else "SUCCESS")
        details = {k: v for k, v in kwargs.items() if k != "status"}
        self._write(op, status, details)

    def _level(self, level: str, *args: Any, **kwargs: Any) -> None:
        self._write(_coerce_op(args, kwargs), level, kwargs)

    def info(self, *args: Any, **kwargs: Any) -> None:
        self._level("INFO", *args, **kwargs)

    def debug(self, *args: Any, **kwargs: Any) -> None:
        self._level("DEBUG", *args, **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        self._level("WARNING", *args, **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> None:
        self._level("ERROR", *args, **kwargs)

    def exception(self, *args: Any, **kwargs: Any) -> None:
        self._level("ERROR", *args, **kwargs)


def get_logger(*_args: Any, **_kwargs: Any) -> ReproducibilityLogger:
    """Return the singleton logger; accepts/ignores any args (e.g. ``__name__``)."""
    return ReproducibilityLogger()


def _safe_log(operation: str, status: str = "SUCCESS", **details: Any) -> None:
    try:
        get_logger().log(operation, status=status, **details)
    except Exception:
        pass


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Polymorphic operation logger — tolerates all usages, never raises:

    1. bare decorator ``@log_operation``;
    2. decorator factory ``@log_operation("name", output_path_arg="p")`` /
       ``@log_operation(operation_name=..., output_path_arg=...)``;
    3. direct call ``log_operation("op", in, out, params, status)`` /
       ``log_operation(operation="op", logger=lg)`` / ``log_operation(lg, "op", {...})``.
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
        return _wrap(args[0], getattr(args[0], "__name__", "operation"))

    # (3) direct-call side effect (harmless for the factory form too).
    _safe_log(_coerce_op(args, kwargs), status=str(kwargs.get("status", "SUCCESS")))

    # (2) decorator factory: return a decorator (direct callers ignore it).
    def decorator(func: Callable) -> Callable:
        return _wrap(func, _coerce_op(args, kwargs) if (args or kwargs) else getattr(func, "__name__", "operation"))

    return decorator
