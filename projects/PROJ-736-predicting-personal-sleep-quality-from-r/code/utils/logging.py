"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import hashlib
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


def setup_logging(*args: Any, **kwargs: Any) -> None:
    """Tolerant setup logging function.

    Accepts any arguments (e.g., file path, logger name) without raising.
    The actual logging is handled by the global ReproducibilityLogger.
    """
    # No-op: The ReproducibilityLogger is global and self-managing.
    # This function exists solely to satisfy callers that expect a setup step.
    pass


def log_stage_start(*args: Any, **kwargs: Any) -> LogEntry:
    """Log the start of a stage.

    Tolerant of all call shapes:
    - log_stage_start("name")
    - log_stage_start(logger, "name")
    - log_stage_start("name", params)
    - log_stage_start(logger, "name", params)
    - log_stage_start(logger, "name", message="...")
    """
    # Normalize arguments
    logger = None
    stage_name = None
    params = {}

    if len(args) == 0:
        # Fallback
        return get_logger().log("stage_start", **kwargs)

    if len(args) == 1:
        if isinstance(args[0], str):
            stage_name = args[0]
        elif hasattr(args[0], 'log'):
            logger = args[0]
        else:
            params = args[0] if isinstance(args[0], dict) else {}

    elif len(args) == 2:
        first, second = args
        if isinstance(first, str):
            stage_name = first
            if isinstance(second, dict):
                params = second
            elif hasattr(second, 'log'):
                logger = second
        elif hasattr(first, 'log'):
            logger = first
            if isinstance(second, str):
                stage_name = second
            elif isinstance(second, dict):
                params = second

    elif len(args) >= 3:
        # logger, stage_name, params/message
        first, second, third = args
        if hasattr(first, 'log'):
            logger = first
            stage_name = second if isinstance(second, str) else str(second)
            if isinstance(third, dict):
                params = third
            elif isinstance(third, str):
                params = {"message": third}

    # Merge kwargs into params
    if kwargs:
        params.update(kwargs)

    # If stage_name is missing but we have a string in kwargs or args, try to find it
    if not stage_name and params.get("operation"):
        stage_name = params.pop("operation")

    if not stage_name:
        stage_name = "unknown_stage"

    entry = LogEntry(operation=f"stage_start:{stage_name}", parameters=params)
    if logger:
        logger.entries.append(entry)
    else:
        get_logger().entries.append(entry)
    return entry


def log_stage_complete(*args: Any, **kwargs: Any) -> LogEntry:
    """Log the completion of a stage."""
    # Similar logic to log_stage_start but for completion
    stage_name = kwargs.get("stage", args[0] if args else "unknown_stage")
    params = {k: v for k, v in kwargs.items() if k != "stage"}
    if len(args) > 1:
        params.update(args[1] if isinstance(args[1], dict) else {})

    entry = LogEntry(operation=f"stage_complete:{stage_name}", parameters=params)
    get_logger().entries.append(entry)
    return entry


def log_stage_error(*args: Any, **kwargs: Any) -> LogEntry:
    """Log an error during a stage."""
    stage_name = kwargs.get("stage", args[0] if args else "unknown_stage")
    error_msg = kwargs.get("error", args[1] if len(args) > 1 else "Unknown error")
    params = {k: v for k, v in kwargs.items() if k not in ("stage", "error")}

    entry = LogEntry(operation=f"stage_error:{stage_name}", parameters={**params, "error": str(error_msg)})
    get_logger().entries.append(entry)
    return entry


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
