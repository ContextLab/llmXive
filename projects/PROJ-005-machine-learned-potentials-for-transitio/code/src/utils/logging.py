"""
Structured logging and progress tracking for the llmXive pipeline.

Provides a custom formatter for JSON-structured logs, setup utilities for
project-wide logger configuration, and helper functions for logging
progress updates, metrics, and error summaries.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Ensure the log directory exists if we are writing to a file
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """
    A logging formatter that outputs log records as JSON.
    Includes timestamp, level, logger name, message, and optional extra data.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    use_json: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with structured JSON formatting.

    Args:
        name: Name of the logger (usually __name__).
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs to stdout.
        use_json: If True, use StructuredFormatter; otherwise, use default format.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    formatter: logging.Formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def log_progress(
    logger: logging.Logger,
    task: str,
    current: int,
    total: int,
    message: Optional[str] = None,
) -> None:
    """
    Log a progress update for a long-running task.

    Args:
        logger: Logger instance.
        task: Name of the task being tracked.
        current: Current step number.
        total: Total number of steps.
        message: Optional additional message.
    """
    percentage = (current / total) * 100 if total > 0 else 0.0
    status = f"Task: {task} | Progress: {current}/{total} ({percentage:.1f}%)"
    if message:
        status += f" | {message}"

    logger.info(status, extra={"extra_data": {"task": task, "current": current, "total": total}})


def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    step: Optional[int] = None,
) -> None:
    """
    Log a scalar metric value.

    Args:
        logger: Logger instance.
        metric_name: Name of the metric.
        value: Numeric value.
        unit: Optional unit of measurement.
        step: Optional step number (e.g., epoch).
    """
    message = f"Metric: {metric_name} = {value}"
    if unit:
        message += f" ({unit})"
    if step is not None:
        message += f" @ step {step}"

    logger.info(message, extra={"extra_data": {"metric": metric_name, "value": value, "unit": unit, "step": step}})


def log_error_summary(
    logger: logging.Logger,
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a structured error summary.

    Args:
        logger: Logger instance.
        error_type: Type of error (e.g., "ValueError", "RuntimeError").
        error_message: Human-readable error message.
        context: Optional dictionary of contextual data.
    """
    message = f"Error: {error_type} - {error_message}"
    logger.error(message, extra={"extra_data": {"error_type": error_type, "message": error_message, "context": context}})


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Convenience function to get a pre-configured logger.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    return setup_logger(name, log_file=LOG_DIR / f"{name}.log")
