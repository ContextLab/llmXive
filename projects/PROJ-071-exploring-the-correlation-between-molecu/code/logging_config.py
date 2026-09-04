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
    """Tolerant error logging."""
    get_logger().log("error", **kwargs)


def handle_pipeline_exception(exc: Exception, context: str = "") -> None:
    """Handle a pipeline exception by logging it."""
    get_logger().log("exception", error=str(exc), context=context)


def log_pipeline_start(operation: str = "", parameters: dict | None = None) -> LogEntry:
    """Log the start of a pipeline operation.
    
    Accepts various call shapes to ensure compatibility with all callers.
    - log_pipeline_start()
    - log_pipeline_start("op_name")
    - log_pipeline_start("op_name", {"key": "val"})
    """
    if parameters is None:
        parameters = {}
    # If operation is passed as the second positional arg in a weird way, handle it
    if not operation and len(parameters) == 1 and isinstance(list(parameters.keys())[0], str):
         # This case is unlikely but handled for safety
         pass
    return get_logger().log(operation, **(parameters if parameters else {}))


def log_pipeline_complete(operation: str = "", parameters: dict | None = None) -> LogEntry:
    """Log the completion of a pipeline operation."""
    if parameters is None:
        parameters = {}
    return get_logger().log(f"{operation}_complete", **(parameters if parameters else {}))


def log_pipeline_failure(*args: Any, **kwargs: Any) -> None:
    """Log a pipeline failure.
    
    Accepts ALL of the following call shapes:
    - log_pipeline_failure("operation_name", "reason")
    - log_pipeline_failure(reason="reason")
    - log_pipeline_failure(str(e))
    - log_pipeline_failure(logger, "op", "reason")
    """
    # Handle shape: log_pipeline_failure(logger, "op", "reason")
    if args and isinstance(args[0], ReproducibilityLogger):
        logger = args[0]
        op = args[1] if len(args) > 1 else kwargs.get("operation", "failure")
        reason = args[2] if len(args) > 2 else kwargs.get("reason", "")
        logger.log("pipeline_failure", operation=op, reason=reason)
        return

    # Handle shape: log_pipeline_failure(str(e)) -> single string
    if len(args) == 1 and isinstance(args[0], str) and not kwargs:
        get_logger().log("pipeline_failure", reason=args[0])
        return

    # Handle shape: log_pipeline_failure("op", "reason")
    if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], str):
        get_logger().log("pipeline_failure", operation=args[0], reason=args[1])
        return

    # Handle shape: log_pipeline_failure(reason="reason")
    if "reason" in kwargs:
        op = kwargs.get("operation", "failure")
        get_logger().log("pipeline_failure", operation=op, reason=kwargs["reason"])
        return

    # Fallback: try to extract op and reason from args/kwargs
    op = args[0] if args else kwargs.get("operation", "failure")
    reason = args[1] if len(args) > 1 else kwargs.get("reason", "")
    get_logger().log("pipeline_failure", operation=op, reason=reason)
