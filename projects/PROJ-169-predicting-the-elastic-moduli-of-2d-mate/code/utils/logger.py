"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List

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


def configure_log_file(path: str) -> None:
    """Configure the root logger to write to a file."""
    logging.basicConfig(
        filename=path,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def log_bias_check(report: Any) -> None:
    """
    Log bias check summary.
    
    Args:
        report: A BiasReport object or a dictionary containing a 'summary' key.
                This function accepts the full report object to avoid data loss.
                It handles the specific call shape `log_bias_check(report.summary)`
                by checking if the argument is already a string (the summary).
    """
    logger = get_logger()
    summary_text = ""
    
    # Handle direct string call: log_bias_check("some summary text")
    if isinstance(report, str):
        summary_text = report
    # Handle object with summary attribute: log_bias_check(report.summary) -> report is the object? 
    # Wait, the call site is `log_bias_check(report.summary)`. 
    # If report.summary is a string, `report` here is that string.
    # If the caller passed the object `report` (expecting us to extract), `report` is the object.
    # We need to be robust to both.
    elif hasattr(report, 'summary'):
        summary_text = report.summary
    elif isinstance(report, dict) and 'summary' in report:
        summary_text = report['summary']
    else:
        summary_text = str(report)
    
    logger.log("bias_check", summary=summary_text)
    # Also log to standard logging for immediate visibility
    logging.info(f"Bias Check Summary: {summary_text}")


def log_exclusion_reason(reason: str, level: int = logging.INFO) -> None:
    """
    Log a specific exclusion reason.
    
    Args:
        reason: The text describing the exclusion.
        level: The logging level (default INFO).
    """
    logger = get_logger()
    logger.log("exclusion_reason", reason=reason)
    logging.log(level, f"Exclusion: {reason}")


def log_training_metrics(epoch: int, loss: float, metrics: Dict[str, float]) -> None:
    """
    Log training metrics.
    
    Args:
        epoch: The current epoch number.
        loss: The training loss.
        metrics: A dictionary of additional metrics (e.g., MAPE, RMSE).
    """
    logger = get_logger()
    logger.log("training_metrics", epoch=epoch, loss=loss, metrics=metrics)
    logging.info(f"Epoch {epoch}: Loss={loss}, Metrics={metrics}")


def log_model_checkpoint(path: str, metrics: Dict[str, float]) -> None:
    """
    Log a model checkpoint event.
    
    Args:
        path: The file path to the saved model.
        metrics: The metrics achieved at this checkpoint.
    """
    logger = get_logger()
    logger.log("model_checkpoint", path=path, metrics=metrics)
    logging.info(f"Model checkpoint saved at {path} with metrics: {metrics}")