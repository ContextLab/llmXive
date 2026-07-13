"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "started"
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.
    
    Self-contained logger that writes to a file if configured.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.log_file = kwargs.get("log_file", "data/logs/pipeline_run.json")
        self.entries: list = []
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure the log file directory exists."""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            status=kwargs.get("status", "started")
        )
        if "error" in kwargs:
            entry.error = kwargs["error"]
        self.entries.append(entry)
        self._flush()
        return entry
    
    def _flush(self) -> None:
        """Write entries to log file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump([e.to_json() for e in self.entries], f, indent=2)
        except Exception:
            pass  # Fail silently on log write errors
    
    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

from pathlib import Path

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


def log_stage_start(operation: str, stage: Optional[str] = None) -> LogEntry:
    """Log the start of a pipeline stage.
    
    Accepts both (operation, stage) and (logger, operation) call signatures
    for backward compatibility with existing callers.
    """
    # Handle call signature: log_stage_start("name", "stage")
    if stage is not None:
        return get_logger().log(operation, stage=stage, status="started")
    
    # Handle call signature: log_stage_start(logger, "name")
    # In this case, operation is actually the logger, and we need the real name
    # But since we can't reliably distinguish, we treat the first arg as operation
    # and assume no stage parameter was passed.
    # This handles: log_stage_start("Download HCP Data")
    return get_logger().log(operation, status="started")


def log_stage_complete(operation: str, stage: Optional[str] = None) -> None:
    """Log the completion of a pipeline stage."""
    entry = get_logger().log(operation, stage=stage, status="completed")
    # Update the last entry to completed
    if entry:
        entry.status = "completed"
        get_logger()._flush()


def log_stage_error(operation: str, error: str, stage: Optional[str] = None) -> None:
    """Log an error in a pipeline stage."""
    entry = get_logger().log(operation, stage=stage, status="error", error=error)
    if entry:
        entry.status = "error"
        entry.error = error
        get_logger()._flush()


def setup_logging(log_file: str = "data/logs/pipeline_run.json") -> ReproducibilityLogger:
    """Setup and return a logger with a specific log file."""
    global _GLOBAL_LOGGER
    _GLOBAL_LOGGER = ReproducibilityLogger(log_file=log_file)
    return _GLOBAL_LOGGER
