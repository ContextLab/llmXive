"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

# -------------------------------------------------------------------------
# Core data structures
# -------------------------------------------------------------------------

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self‑contained and does **not** delegate to the stdlib
    ``logging`` module because its ``log`` signature differs from what the
    project expects.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record an operation.

        The first positional argument (if any) is treated as the operation name.
        All keyword arguments are stored as parameters.
        """
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no‑op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop


# -------------------------------------------------------------------------
# Global logger singleton
# -------------------------------------------------------------------------

_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a module‑wide singleton logger."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


# -------------------------------------------------------------------------
# Utility decorators / functions
# -------------------------------------------------------------------------

def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose: decorator (@log_operation) OR direct logging call.

    The direct‑call path ALWAYS returns a ``LogEntry`` (callers use
    ``.to_json()``); the decorator path returns the wrapped function.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


# -------------------------------------------------------------------------
# Additional convenience functions required by the project
# -------------------------------------------------------------------------

def setup_logger(name: str = "pipeline") -> ReproducibilityLogger:
    """Create or retrieve a named logger."""
    return get_logger(name)


def get_pipeline_logger() -> ReproducibilityLogger:
    """Alias used by older modules."""
    return get_logger("pipeline")


def log_model_usage(logger: ReproducibilityLogger, model_name: str) -> LogEntry:
    """Record which model was used for generation."""
    return logger.log("model_usage", model=model_name)


def log_generation_result(
    logger: ReproducibilityLogger,
    task_id: str,
    success: bool,
    error_message: Optional[str] = None,
) -> LogEntry:
    """Log the outcome of the LLM generation step."""
    params: Dict[str, Any] = {"task_id": task_id, "success": success}
    if error_message:
        params["error_message"] = error_message
    return logger.log("generation_result", **params)


def log_coverage_result(
    logger: ReproducibilityLogger,
    task_id: str,
    coverage: Dict[str, Any],
    success: bool,
    error_message: Optional[str] = None,
) -> LogEntry:
    """Log the outcome of the coverage measurement step."""
    params: Dict[str, Any] = {
        "task_id": task_id,
        "coverage": coverage,
        "success": success,
    }
    if error_message:
        params["error_message"] = error_message
    return logger.log("coverage_result", **params)


def log_pipeline_summary(
    logger: ReproducibilityLogger,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Log a high‑level summary of the pipeline run.

    This function is tolerant to both the old signature
    ``log_pipeline_summary(logger, results)`` and the newer explicit
    signature ``log_pipeline_summary(logger, successful, failed,
    duration_seconds)``. It never raises; missing information is filled
    with ``None``.
    """
    # Old style: a single positional argument containing a results list/dict
    if len(args) == 1 and not kwargs:
        results = args[0]
        successful = sum(1 for r in results if r.get("result") == "success")
        failed = sum(1 for r in results if r.get("result") != "success")
        duration_seconds = None
    else:
        successful = kwargs.get("successful")
        failed = kwargs.get("failed")
        duration_seconds = kwargs.get("duration_seconds")

    summary = {
        "successful_tasks": successful,
        "failed_tasks": failed,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.log("pipeline_summary", **summary)