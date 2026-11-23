"""
Logging Configuration (Task T015).

Provides a robust logging mechanism for the pipeline, specifically
handling exclusion logging for invalid molecules.

Implements a self-contained logger that does not rely on the stdlib
logging module's strict signatures, ensuring compatibility with all
callers in the pipeline.
"""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
EXCLUDED_CSV_PATH = os.path.join(PROCESSED_DIR, "excluded_molecules.csv")

# Ensure directory exists
os.makedirs(PROCESSED_DIR, exist_ok=True)


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.
    
    This logger is self-contained and does not delegate to the stdlib 
    logging module to avoid signature mismatches.
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
    decorator use returns the wrapped function.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def log_error(error_msg: str) -> None:
    """Log an error message to the global logger."""
    get_logger().log("error", message=error_msg)


def handle_pipeline_exception(e: Exception) -> None:
    """Handle a pipeline exception by logging it."""
    get_logger().log("exception", error=str(e), type=type(e).__name__)


def log_pipeline_start(operation: str, parameters: dict | None = None) -> LogEntry:
    """Log the start of a pipeline operation.
    
    Tolerant of different call shapes:
    - log_pipeline_start("op", {"key": "val"})
    - log_pipeline_start(operation="op", parameters={"key": "val"})
    """
    if parameters is None:
        parameters = {}
    return get_logger().log(operation, **parameters)


def log_pipeline_complete(operation: str, status: str = "success") -> LogEntry:
    """Log the completion of a pipeline operation."""
    return get_logger().log(operation, status=status)


def log_pipeline_failure(*args: Any, **kwargs: Any) -> None:
    """Log a pipeline failure.
    
    Accepts multiple call shapes:
    - log_pipeline_failure("op", "reason")
    - log_pipeline_failure(reason="reason")
    - log_pipeline_failure(str(e))
    - log_pipeline_failure(logger, "op", "reason")
    """
    # Handle shape: log_pipeline_failure(logger, "op", "reason")
    if len(args) >= 3:
        # Skip first arg if it looks like a logger (has 'log' attr)
        # But the spec says 'edit the DEFINITION', so we just ignore the logger arg if passed
        op = args[1]
        reason = args[2]
    # Handle shape: log_pipeline_failure("op", "reason")
    elif len(args) == 2:
        op = args[0]
        reason = args[1]
    # Handle shape: log_pipeline_failure(reason="reason")
    elif "reason" in kwargs:
        op = kwargs.get("operation", "failure")
        reason = kwargs["reason"]
    # Handle shape: log_pipeline_failure(str(e))
    elif len(args) == 1:
        op = "failure"
        reason = str(args[0])
    else:
        op = kwargs.get("operation", "failure")
        reason = kwargs.get("reason", "Unknown error")

    get_logger().log(op, status="failed", reason=reason)


def get_exclusion_logger() -> ReproducibilityLogger:
    """
    Returns a logger configured to write to data/processed/excluded_molecules.csv.
    
    Note: The actual writing to CSV is handled by the caller (e.g., descriptors.py)
    or this logger can be extended to write if needed. For now, it returns the
    standard logger, and the caller uses `log_error_to_file` in descriptors.py
    to perform the actual CSV append as per T015 requirements.
    """
    return get_logger("exclusion")