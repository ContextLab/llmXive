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


def log_error(*args: Any, **kwargs: Any) -> None:
    """Log an error message."""
    logger = get_logger()
    logger.log("error", **kwargs)


def handle_pipeline_exception(exception: Exception) -> None:
    """Handle a pipeline exception."""
    logger = get_logger()
    logger.log("pipeline_exception", error=str(exception))


def log_pipeline_start(operation: str = "pipeline", **kwargs: Any) -> None:
    """Log the start of a pipeline operation."""
    logger = get_logger()
    logger.log("pipeline_start", operation=operation, **kwargs)


def log_pipeline_complete(operation: str = "pipeline", **kwargs: Any) -> None:
    """Log the completion of a pipeline operation."""
    logger = get_logger()
    logger.log("pipeline_complete", operation=operation, **kwargs)


def log_pipeline_failure(*args: Any, **kwargs: Any) -> None:
    """Log a pipeline failure. Accepts multiple call shapes."""
    logger = get_logger()
    # Handle various call shapes:
    # log_pipeline_failure("op", "reason")
    # log_pipeline_failure(reason="reason")
    # log_pipeline_failure(str(e))
    # log_pipeline_failure(logger, "op", "reason") -> ignore first arg if logger
    
    op = ""
    reason = ""
    
    # Filter out logger instances from args
    clean_args = [a for a in args if not isinstance(a, ReproducibilityLogger)]
    
    if len(clean_args) >= 2:
        op = str(clean_args[0])
        reason = str(clean_args[1])
    elif len(clean_args) == 1:
        reason = str(clean_args[0])
    
    if "operation" in kwargs:
        op = kwargs["operation"]
    if "reason" in kwargs:
        reason = kwargs["reason"]
        
    logger.log("pipeline_failure", operation=op, reason=reason, **kwargs)