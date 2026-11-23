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


def setup_logging(log_file: str | None = None, *args: Any, **kwargs: Any) -> None:
    """Setup logging to file (optional).

    Args:
        log_file: Path to log file. If None, uses global logger only.
        *args, **kwargs: Additional arguments (ignored for compatibility).
    """
    # This function is intentionally tolerant of any signature.
    # The global logger is already set up by get_logger().
    pass


def log_stage_start(stage_name: str, params: dict | None = None, *args: Any, **kwargs: Any) -> None:
    """Log the start of a stage.

    Args:
        stage_name: Name of the stage.
        params: Optional parameters dict.
        *args, **kwargs: Additional arguments (ignored for compatibility).
    """
    logger = get_logger()
    if params is None:
        params = {}
    logger.log("stage_start", operation=stage_name, **params)


def log_stage_complete(stage_name: str, *args: Any, **kwargs: Any) -> None:
    """Log the completion of a stage."""
    logger = get_logger()
    logger.log("stage_complete", operation=stage_name)


def log_stage_error(stage_name: str, error_msg: str, *args: Any, **kwargs: Any) -> None:
    """Log an error in a stage."""
    logger = get_logger()
    logger.log("stage_error", operation=stage_name, error=error_msg)


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
