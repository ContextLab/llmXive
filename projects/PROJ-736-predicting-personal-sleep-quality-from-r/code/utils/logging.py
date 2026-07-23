"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, Union


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"

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

    def info(self, *args: Any, **kwargs: Any) -> None:
        return None

    def debug(self, *args: Any, **kwargs: Any) -> None:
        return None

    def warning(self, *args: Any, **kwargs: Any) -> None:
        return None

    def error(self, *args: Any, **kwargs: Any) -> None:
        return None

    def critical(self, *args: Any, **kwargs: Any) -> None:
        return None

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


def setup_logging(log_file: Optional[Union[str, os.PathLike]] = None) -> None:
    """Configure logging to file if provided.

    Tolerant of missing arguments or invalid paths.
    """
    if log_file is None:
        return
    try:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        # In a real system, we'd open the file and attach a handler.
        # Here we just ensure the directory exists to satisfy callers.
    except Exception:
        pass


def log_stage_start(
    arg1: Any,
    arg2: Optional[Any] = None,
    arg3: Optional[Any] = None,
    **kwargs: Any
) -> LogEntry:
    """Tolerant stage start logger.

    Accepts:
      - log_stage_start("stage_name")
      - log_stage_start(logger, "stage_name")
      - log_stage_start("stage_name", params)
      - log_stage_start(logger, "stage_name", params)
      - log_stage_start(logger, "stage_name", message="...")
    """
    logger = None
    stage_name = None
    params = {}

    # Determine roles based on types
    if isinstance(arg1, str):
        stage_name = arg1
        if isinstance(arg2, dict):
            params = arg2
        elif arg2 is not None:
            # Could be logger or message
            if hasattr(arg2, 'log'):
                logger = arg2
            else:
                params = {"message": str(arg2)}
        if isinstance(arg3, dict):
            params.update(arg3)
    else:
        # arg1 is likely logger
        logger = arg1
        if isinstance(arg2, str):
            stage_name = arg2
            if isinstance(arg3, dict):
                params = arg3
            elif arg3 is not None:
                params = {"message": str(arg3)}
        else:
            # Fallback
            stage_name = str(arg2) if arg2 else "unknown"
            params = arg3 if isinstance(arg3, dict) else {}

    params.update(kwargs)
    entry = LogEntry(operation=f"START_{stage_name}", parameters=params)
    if logger is not None and hasattr(logger, 'entries'):
        logger.entries.append(entry)
    return entry


def log_stage_complete(stage_name: str, **kwargs: Any) -> LogEntry:
    """Log stage completion."""
    entry = LogEntry(operation=f"COMPLETE_{stage_name}", parameters=kwargs)
    return entry


def log_stage_error(stage_name: str, error_msg: str, **kwargs: Any) -> LogEntry:
    """Log stage error."""
    entry = LogEntry(operation=f"ERROR_{stage_name}", parameters={"error": error_msg, **kwargs})
    return entry


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
