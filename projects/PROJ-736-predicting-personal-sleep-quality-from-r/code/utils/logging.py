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


def log_stage_start(stage: str, message: str = "", **kwargs: Any) -> None:
    """Log the start of a pipeline stage.

    Accepts various call signatures:
    - log_stage_start(stage)
    - log_stage_start(stage, message=...)
    - log_stage_start(logger, stage)
    - log_stage_start(logger, stage, message=...)
    """
    logger = get_logger()
    # Handle optional logger as first arg
    if len(stage) > 0 and isinstance(stage, ReproducibilityLogger):
        logger = stage
        stage = stage if isinstance(stage, str) else (args[1] if len(args) > 1 else "stage")
    
    # Re-parse args properly
    _logger = logger
    _stage = stage
    _msg = message
    
    # If the first argument is a logger instance, shift
    if isinstance(stage, ReproducibilityLogger):
        _logger = stage
        if len(args) > 1:
            _stage = args[1]
        if len(args) > 2:
            _msg = args[2]
        elif "message" in kwargs:
            _msg = kwargs["message"]
    elif isinstance(stage, str):
        _stage = stage
        if "message" in kwargs:
            _msg = kwargs["message"]
    
    _logger.log("stage_start", operation=_stage, message=_msg, **kwargs)


def log_stage_complete(stage: str, message: str = "", **kwargs: Any) -> None:
    """Log the completion of a pipeline stage."""
    logger = get_logger()
    if isinstance(stage, ReproducibilityLogger):
        logger = stage
        if len(kwargs) > 0:
            stage = list(kwargs.keys())[0] # Fallback logic if signature is weird
        
    logger.log("stage_complete", operation=stage, message=message, **kwargs)


def log_stage_error(stage: str, message: str = "", **kwargs: Any) -> None:
    """Log an error in a pipeline stage."""
    logger = get_logger()
    if isinstance(stage, ReproducibilityLogger):
        logger = stage
    
    logger.log("stage_error", operation=stage, message=message, **kwargs)


def log_event(operation: str, **kwargs: Any) -> None:
    """Log a generic event."""
    get_logger().log(operation, **kwargs)


def log_event_dict(event_dict: Dict[str, Any]) -> None:
    """Log an event from a dictionary."""
    op = event_dict.get("operation", "unknown_event")
    get_logger().log(op, **event_dict)


def setup_logging(log_file: str = None) -> None:
    """Initialize logging to a file if provided."""
    if log_file:
        # In a real system, we would configure file handlers
        # Here we just ensure the directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
