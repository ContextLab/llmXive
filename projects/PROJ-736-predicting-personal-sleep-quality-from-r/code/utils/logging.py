"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# Ensure log directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "pipeline_run.json")


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self-contained and writes to `data/logs/pipeline_run.json`.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        self._write_entry(entry)
        return entry

    def _write_entry(self, entry: LogEntry) -> None:
        """Append a single JSON line to the log file."""
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
        except Exception:
            # Fail silently to avoid breaking the pipeline if logging fails
            pass

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


def log_stage_start(stage_name: str, parameters: dict | None = None) -> LogEntry:
    """Log the start of a pipeline stage.

    Accepts:
      - log_stage_start("stage_name")
      - log_stage_start(logger, "stage_name")
      - log_stage_start("stage_name", {"key": "value"})
      - log_stage_start(logger, "stage_name", {"key": "value"})
    """
    logger = None
    name = stage_name
    params = parameters or {}

    # Handle flexible argument shapes
    if isinstance(stage_name, ReproducibilityLogger):
        logger = stage_name
        if parameters:
            if isinstance(parameters, str):
                # log_stage_start(logger, "stage_name") -> params is actually stage_name
                name = parameters
                params = {}
            else:
                # log_stage_start(logger, "stage_name", params)
                name = parameters.get("stage_name", parameters.get("name", "unknown"))
                params = parameters if isinstance(parameters, dict) else {}
        else:
            # log_stage_start(logger, "stage_name")
            name = stage_name
            params = {}
    elif parameters and isinstance(parameters, dict):
        # log_stage_start("stage_name", params)
        name = stage_name
        params = parameters
    elif parameters and isinstance(parameters, str):
        # log_stage_start(logger, "stage_name") where second arg is string
        logger = ReproducibilityLogger() # fallback if logger was expected but passed as string?
        # Actually, if first arg is string and second is string, it's likely log_stage_start(logger, "name")
        # But we don't have a logger here. Let's assume standard: log_stage_start("name", params)
        # If params is string, treat as name? No, signature says parameters is dict.
        # Let's stick to: if first is string, it's name.
        name = stage_name
        params = {}

    # If we still have a logger passed as first arg (checked above), use it, else global
    effective_logger = logger if logger else get_logger()

    entry = effective_logger.log(f"Start {name}", stage=name, **params)
    return entry


def log_stage_complete(stage_name: str, message: str | None = None) -> None:
    """Log the successful completion of a stage."""
    logger = get_logger()
    params = {"stage": stage_name}
    if message:
        params["message"] = message
    logger.log(f"Complete {stage_name}", **params)


def log_stage_error(stage_name: str, error: str | Exception) -> None:
    """Log an error during a stage."""
    logger = get_logger()
    err_str = str(error)
    logger.log(f"Error {stage_name}", stage=stage_name, error=err_str)


def setup_logging() -> None:
    """Initialize logging (no-op for this self-contained logger, but kept for API compatibility)."""
    pass
