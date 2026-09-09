"""
Structured logging and progress tracking for the ML Potential pipeline.

Provides a consistent logging interface across all modules, including:
- Structured JSON formatting for log lines
- Progress tracking for long-running operations
- Metric logging for experiment tracking
- Error summary aggregation
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines for structured logging.
    Includes timestamp, level, module, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    console_output: bool = True,
    json_format: bool = True,
) -> logging.Logger:
    """
    Set up a logger with optional file output and structured formatting.

    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file. If provided, logs are written here.
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        console_output: Whether to log to console
        json_format: Whether to use structured JSON formatting

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log_file is provided
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_progress(
    logger: logging.Logger,
    task: str,
    current: int,
    total: int,
    message: Optional[str] = None,
    level: int = logging.INFO,
) -> None:
    """
    Log progress for a long-running operation.

    Args:
        logger: Logger instance to use
        task: Name of the task being performed
        current: Current progress count
        total: Total expected count
        message: Optional additional message
        level: Log level for this message
    """
    progress_data = {
        "task": task,
        "current": current,
        "total": total,
        "percent": (current / total * 100) if total > 0 else 0,
    }

    if message:
        progress_data["message"] = message

    logger.log(
        level,
        f"Progress: {task} - {current}/{total} ({progress_data['percent']:.1f}%)",
        extra={"extra_fields": progress_data},
    )


def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Union[int, float],
    unit: Optional[str] = None,
    stage: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a metric value for experiment tracking.

    Args:
        logger: Logger instance to use
        metric_name: Name of the metric
        value: Metric value
        unit: Optional unit of measurement
        stage: Optional stage identifier (e.g., "training", "validation", "test")
        metadata: Optional additional metadata
    """
    metric_data = {
        "metric_name": metric_name,
        "value": value,
    }

    if unit:
        metric_data["unit"] = unit

    if stage:
        metric_data["stage"] = stage

    if metadata:
        metric_data["metadata"] = metadata

    logger.info(
        f"Metric: {metric_name} = {value}",
        extra={"extra_fields": metric_data},
    )


def log_error_summary(
    logger: logging.Logger,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    recoverable: bool = False,
) -> None:
    """
    Log an error summary with optional recovery status.

    Args:
        logger: Logger instance to use
        error_type: Type of error (e.g., "ValidationError", "DataError")
        message: Human-readable error message
        details: Optional dictionary of additional error details
        recoverable: Whether this error is recoverable
    """
    error_data = {
        "error_type": error_type,
        "recoverable": recoverable,
    }

    if details:
        error_data["details"] = details

    log_level = logging.WARNING if recoverable else logging.ERROR

    logger.log(
        log_level,
        f"Error [{error_type}]: {message}",
        extra={"extra_fields": error_data},
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default configuration.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)