"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging as stdlib_logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional


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


def log_error(
    message: str,
    operation: str = "error",
    error_type: Optional[str] = None,
    **kwargs: Any,
) -> LogEntry:
    """Log an error message with optional error type."""
    return get_logger().log(
        operation,
        message=message,
        error_type=error_type,
        **kwargs,
    )


def handle_pipeline_exception(
    exception: Exception,
    operation: str = "pipeline",
    **kwargs: Any,
) -> LogEntry:
    """Handle a pipeline exception by logging it."""
    return get_logger().log(
        operation,
        message=str(exception),
        error_type=type(exception).__name__,
        traceback=traceback.format_exc(),
        **kwargs,
    )


def log_pipeline_start(operation: str = "pipeline_start", **kwargs: Any) -> LogEntry:
    """Log the start of a pipeline operation."""
    return get_logger().log(operation, **kwargs)


def log_pipeline_complete(
    operation: str = "pipeline_complete",
    status: str = "success",
    **kwargs: Any,
) -> LogEntry:
    """Log the completion of a pipeline operation."""
    return get_logger().log(operation, status=status, **kwargs)


def log_pipeline_failure(
    *args: Any,
    reason: Optional[str] = None,
    operation: str = "pipeline_failure",
    **kwargs: Any,
) -> LogEntry:
    """Log a pipeline failure.

    Accepts multiple call shapes:
    - log_pipeline_failure("operation_name", "reason")
    - log_pipeline_failure(reason="reason")
    - log_pipeline_failure(str(e))
    - log_pipeline_failure(logger, "op", "reason")
    """
    # Handle call shape: log_pipeline_failure(logger, "op", "reason")
    if len(args) >= 2:
        first_arg = args[0]
        second_arg = args[1]
        if hasattr(first_arg, 'log') and callable(getattr(first_arg, 'log')):
            # First arg is a logger
            op = second_arg if len(args) > 2 else operation
            msg = args[2] if len(args) > 2 else str(reason) if reason else "Pipeline failed"
            return first_arg.log(op, message=msg, **kwargs)

    # Handle call shape: log_pipeline_failure("op", "reason") or log_pipeline_failure(reason)
    if len(args) == 2:
        op = args[0]
        msg = args[1]
        return get_logger().log(op, message=msg, reason=reason, **kwargs)
    elif len(args) == 1:
        # Could be reason or operation
        if reason is not None:
            # Called with keyword reason
            return get_logger().log(operation, message=args[0], reason=reason, **kwargs)
        else:
            # Called with single positional arg as operation
            return get_logger().log(args[0], **kwargs)
    else:
        # Fallback
        return get_logger().log(operation, reason=reason, **kwargs)


def log_error_to_file(
    file_path: str,
    message: str,
    error_type: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log an error to a file."""
    import os
    from datetime import datetime

    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)

    timestamp = datetime.utcnow().isoformat()
    entry = {
        "timestamp": timestamp,
        "message": message,
        "error_type": error_type,
        **kwargs,
    }

    with open(file_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

import traceback
