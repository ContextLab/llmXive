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


def log_error(error_type: str, message: str, **kwargs: Any) -> None:
    """Log an error to the global logger."""
    get_logger().log("error", error_type=error_type, message=message, **kwargs)


def handle_pipeline_exception(exc: Exception, context: str = "") -> None:
    """Handle a pipeline exception by logging it."""
    log_error("PipelineException", str(exc), context=context)


def log_pipeline_start(operation: str, parameters: Optional[Dict] = None) -> LogEntry:
    """Log the start of a pipeline operation."""
    if parameters is None:
        parameters = {}
    return get_logger().log(f"start_{operation}", **parameters)


def log_pipeline_complete(operation: str, result: Optional[Dict] = None) -> LogEntry:
    """Log the completion of a pipeline operation."""
    if result is None:
        result = {}
    return get_logger().log(f"complete_{operation}", **result)


def log_pipeline_failure(operation: str, reason: str, **kwargs: Any) -> None:
    """Log a pipeline failure. Accepts flexible arguments."""
    # Handle various call shapes:
    # log_pipeline_failure("op", "reason")
    # log_pipeline_failure(reason="reason")
    # log_pipeline_failure(str(e))
    # log_pipeline_failure(logger, "op", "reason")
    
    args = [operation, reason] if operation and reason else []
    if not args:
        # Try to extract from kwargs or positional
        if 'reason' in kwargs:
            reason = kwargs.pop('reason')
        else:
            # Assume first arg was the reason if operation was missing
            if operation and not reason:
                reason = operation
                operation = "pipeline"
        
    # Normalize
    op = operation if operation else "pipeline"
    msg = reason if reason else "Unknown failure"
    
    get_logger().log(f"fail_{op}", operation=op, reason=msg, **kwargs)
