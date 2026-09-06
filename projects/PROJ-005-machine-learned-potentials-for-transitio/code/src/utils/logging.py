"""
Structured logging and progress tracking utilities for the llmXive pipeline.

This module provides:
- A custom JSON formatter for structured logs.
- A factory to set up project-specific loggers.
- Helper functions to log progress, metrics, and error summaries.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import get_project_root


class StructuredFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON lines.
    This facilitates parsing logs by downstream tools and aggregators.

    The JSON structure includes:
    - timestamp (ISO 8601)
    - level
    - logger_name
    - message
    - extra fields (if any)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields passed in the log call
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Handle standard extra attributes if needed
        if record.__dict__.get("exc_text"):
            # Already formatted by standard formatter if we wanted, but we handle above
            pass

        return json.dumps(log_data)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.

    Args:
        name: The name of the logger (usually __name__).
        level: The logging level (e.g., logging.DEBUG).
        log_file: Optional path to a log file. If provided, logs are written there.
        console: If True, also logs to stdout.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = StructuredFormatter()

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_progress(
    logger: logging.Logger,
    stage: str,
    current: int,
    total: int,
    message: Optional[str] = None,
) -> None:
    """
    Log a progress update as a structured event.

    Args:
        logger: The logger to use.
        stage: Name of the current stage (e.g., "Ingestion", "Training").
        current: Current count (e.g., items processed).
        total: Total expected count.
        message: Optional additional context message.
    """
    percentage = (current / total * 100) if total > 0 else 0.0
    msg = message or f"{stage}: {current}/{total} ({percentage:.1f}%)"

    extra_data = {
        "stage": stage,
        "current": current,
        "total": total,
        "percentage": round(percentage, 2),
    }
    if message:
        extra_data["details"] = message

    # Create a log record with extra data
    logger.info(msg, extra={"extra_data": extra_data})


def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Union[int, float],
    unit: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a specific metric value in a structured format.

    Args:
        logger: The logger to use.
        metric_name: Name of the metric (e.g., "mae", "accuracy").
        value: The numeric value.
        unit: Optional unit string (e.g., "eV").
        context: Optional dictionary of additional context (e.g., {"epoch": 5}).
    """
    extra_data = {
        "metric": metric_name,
        "value": value,
        "unit": unit,
    }
    if context:
        extra_data["context"] = context

    logger.info(f"Metric: {metric_name} = {value}", extra={"extra_data": extra_data})


def log_error_summary(
    logger: logging.Logger,
    error_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error summary for tracking failures.

    Args:
        logger: The logger to use.
        error_type: Category of error (e.g., "DataError", "ModelError").
        description: Human-readable description.
        details: Optional dictionary of technical details.
    """
    extra_data = {
        "error_type": error_type,
        "description": description,
    }
    if details:
        extra_data["details"] = details

    logger.error(f"Error [{error_type}]: {description}", extra={"extra_data": extra_data})


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is not provided, defaults to 'llmXive'.
    This ensures a consistent logger name across the project.

    Args:
        name: Optional logger name.

    Returns:
        A logger instance.
    """
    if name is None:
        name = "llmXive"
    return logging.getLogger(name)
