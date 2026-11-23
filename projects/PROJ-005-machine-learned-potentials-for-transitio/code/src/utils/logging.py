"""
Structured logging and progress tracking for the llmXive pipeline.

This module provides:
- A custom JSON formatter for structured logs.
- A centralized logger setup that respects project configuration.
- Helper functions for logging progress, metrics, and error summaries.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Constants for log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

class StructuredFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records as JSON.
    Ensures machine-parsable logs for automated analysis.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if provided
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)

def setup_logger(
    name: str = "llmXive",
    level: Union[str, int] = "INFO",
    log_file: Optional[Path] = None,
    use_json: bool = True
) -> logging.Logger:
    """
    Configures and returns a logger with structured JSON formatting.

    Args:
        name: Name of the logger.
        level: Logging level (string or int).
        log_file: Optional path to a log file. If provided, logs are written to disk.
        use_json: If True, uses StructuredFormatter; otherwise, uses standard format.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level if isinstance(level, int) else LOG_LEVELS.get(level, logging.INFO))
    logger.propagate = False

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Determine formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves an existing logger or creates a default one if not found.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Fallback to default setup if not explicitly configured
        return setup_logger(name=name)
    return logger

def log_progress(
    logger: logging.Logger,
    task_name: str,
    current: int,
    total: int,
    stage: str = "processing"
) -> None:
    """
    Logs a structured progress update.

    Args:
        logger: The logger instance.
        task_name: Name of the current task.
        current: Current step number.
        total: Total steps.
        stage: Description of the current stage.
    """
    percentage = (current / total * 100) if total > 0 else 0.0
    extra = {
        "task": task_name,
        "stage": stage,
        "current": current,
        "total": total,
        "percentage": round(percentage, 2)
    }
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0,
        f"Progress: {task_name} [{stage}] {current}/{total} ({percentage:.2f}%)",
        (), None
    )
    record.extra_data = extra
    logger.handle(record)

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a structured metric update.

    Args:
        logger: The logger instance.
        metric_name: Name of the metric.
        value: Numeric value of the metric.
        unit: Optional unit string.
        context: Optional dictionary of additional context.
    """
    extra = {
        "metric": metric_name,
        "value": value,
        "unit": unit,
        "context": context or {}
    }
    msg = f"Metric: {metric_name} = {value}" + (f" ({unit})" if unit else "")
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, msg, (), None
    )
    record.extra_data = extra
    logger.handle(record)

def log_error_summary(
    logger: logging.Logger,
    error_count: int,
    error_types: Dict[str, int],
    fatal: bool = False
) -> None:
    """
    Logs a summary of errors encountered during execution.

    Args:
        logger: The logger instance.
        error_count: Total number of errors.
        error_types: Dictionary mapping error type names to counts.
        fatal: If True, logs as CRITICAL; otherwise ERROR.
    """
    level = logging.CRITICAL if fatal else logging.ERROR
    msg = f"Error Summary: {error_count} errors encountered."
    extra = {
        "total_errors": error_count,
        "error_breakdown": error_types
    }
    record = logger.makeRecord(
        logger.name, level, "", 0, msg, (), None
    )
    record.extra_data = extra
    logger.handle(record)