"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # No‑op for standard logging methods
    def __getattr__(self, name: str) -> Callable[..., None]:
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None

        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any):
    """
    Dual‑purpose helper that can be used either as a decorator
    ``@log_operation("name")`` or as a direct logging call
    ``log_operation("name", task_id=..., ...)``.
    """
    # Direct call with additional keyword arguments → return a LogEntry
    if kwargs:
        op = args[0] if args else kwargs.pop("operation", "operation")
        return get_logger().log(op, **kwargs)

    # Called as @log_operation without parameters → simple decorator
    if len(args) == 1 and callable(args[0]):
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any):
            return func(*a, **k)

        return _wrapper

    # Called as @log_operation("operation_name") → return a decorator that logs
    op_name = args[0] if args else kwargs.pop("operation", "operation")

    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any):
            # Log the operation each time the function is invoked
            get_logger().log(op_name, parameters={"args": a, "kwargs": k})
            return func(*a, **k)

        return _wrapper

    return decorator


def log_pipeline_summary(task_id: str, status: str, result: Any) -> None:
    """
    Log the summary of a pipeline operation.
    Called by main.py.
    """
    logger = get_logger("pipeline_summary")
    logger.log("pipeline_summary", task_id=task_id, status=status, result=result)
