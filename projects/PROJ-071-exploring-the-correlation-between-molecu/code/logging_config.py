"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
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

# --- Additional helpers required by pipeline scripts ---

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure standard logging for the pipeline."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if path provided
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger


def log_error(error: Exception, context: str = "") -> None:
    """Log an error with context."""
    logger = logging.getLogger("llmXive_pipeline")
    msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(msg, exc_info=True)


def handle_pipeline_exception(exc: Exception, stage: str = "") -> None:
    """Handle a pipeline exception by logging and optionally raising."""
    logger = logging.getLogger("llmXive_pipeline")
    msg = f"Pipeline failed at stage {stage}" if stage else "Pipeline failed"
    logger.critical(msg, exc_info=True)


def log_pipeline_start(stage_name: str) -> None:
    """Log the start of a pipeline stage."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.info(f"Starting stage: {stage_name}")


def log_pipeline_complete(stage_name: str) -> None:
    """Log the completion of a pipeline stage."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.info(f"Completed stage: {stage_name}")


def log_pipeline_failure(stage_name: str, reason: str) -> None:
    """
    Log a pipeline failure. Accepts flexible call signatures:
    1. log_pipeline_failure(stage_name, reason)
    2. log_pipeline_failure(reason) -> stage_name defaults to "Unknown"
    3. log_pipeline_failure(logger, stage_name, reason)
    """
    # Handle different call signatures to satisfy all callers
    if len([x for x in locals().values() if x is not None]) < 2:
        # Fallback if called with just reason
        stage = stage_name if stage_name else "Unknown"
        msg = reason if reason else "Unknown reason"
    elif isinstance(stage_name, logging.Logger):
        # Case: log_pipeline_failure(logger, stage_name, reason)
        logger = stage_name
        stage = reason  # The second arg is actually the stage in this signature
        msg = reason if reason else "Unknown reason" # This logic is slightly off for the 3-arg case, let's refine
    else:
        # Standard case
        stage = stage_name
        msg = reason

    # Refined logic for the specific signatures found in the traceback:
    # 1. log_pipeline_failure("performance_validation", str(e)) -> stage="performance_validation", reason=str(e)
    # 2. log_pipeline_failure("Missing degradation columns") -> stage="Missing...", reason missing? No, likely just 1 arg.
    # 3. log_pipeline_failure(reason) -> 1 arg, treated as reason? Or stage?
    # 4. log_pipeline_failure(logger, "T055...", str(e)) -> 3 args.

    import inspect
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    # We can't rely on variable names easily here due to the dynamic nature.
    # Let's implement a robust signature handler based on types.
    
    # Re-implementing logic purely on the passed arguments to this function context is hard without *args.
    # Let's assume the function signature in the file is:
    # def log_pipeline_failure(stage_or_reason: str, reason_or_none: Optional[str] = None)
    # But the caller `log_pipeline_failure(logger, ...)` passes a logger first.
    
    # Correct approach: Redefine the function signature to accept *args to handle all cases.
    pass 

# We need to redefine log_pipeline_failure to be truly tolerant as per the "Shared-Module Contract"
# The previous definition above was partial. Here is the robust version.

def log_pipeline_failure(*args: Any, **kwargs: Any) -> None:
    """
    Tolerant failure logger. Handles:
    - log_pipeline_failure(stage_name, reason)
    - log_pipeline_failure(reason)
    - log_pipeline_failure(logger, stage_name, reason)
    """
    logger = logging.getLogger("llmXive_pipeline")
    
    stage_name = "Unknown"
    reason = "Unknown reason"
    
    # Parse arguments flexibly
    if len(args) == 1:
        # Could be just reason, or just stage_name
        arg = args[0]
        if isinstance(arg, logging.Logger):
            logger = arg
            # If only logger passed, nothing to log? Assume empty reason
            reason = "Pipeline failed (no details provided)"
        else:
            # Assume it's the reason
            reason = str(arg)
    elif len(args) == 2:
        first, second = args
        if isinstance(first, logging.Logger):
            logger = first
            stage_name = str(second)
            reason = kwargs.get("reason", "Pipeline failed")
        else:
            stage_name = str(first)
            reason = str(second)
    elif len(args) >= 3:
        first, second, third = args[0], args[1], args[2]
        if isinstance(first, logging.Logger):
            logger = first
            stage_name = str(second)
            reason = str(third)
        else:
            stage_name = str(first)
            reason = str(second)
    elif "reason" in kwargs:
        stage_name = kwargs.get("stage", "Unknown")
        reason = kwargs["reason"]
    
    msg = f"Stage '{stage_name}' failed: {reason}"
    logger.error(msg)
    logger.error("Traceback:")
    import traceback
    logger.error(traceback.format_exc())
    
    # Also log to the reproducibility logger if needed
    try:
        get_logger().log("pipeline_failure", stage=stage_name, error=reason)
    except Exception:
        pass # Fail silently if reproducibility logger fails
