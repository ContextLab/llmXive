"""
Structured logging and progress tracking for the llmXive pipeline.

This module provides:
- A centralized logger configuration that supports JSON-structured output.
- Progress tracking utilities for long-running tasks (e.g., data ingestion, model training).
- Integration with the project's config system (src.utils.config).
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import load_config, get_project_root


# Constants
DEFAULT_LOG_LEVEL = "INFO"
LOG_FILE_NAME = "pipeline.log"
PROGRESS_INTERVAL = 10  # Log progress every N percent
LOG_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_json)s"


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON for structured parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra JSON fields if present
        if hasattr(record, "extra_json"):
            log_entry["data"] = record.extra_json

        return json.dumps(log_entry)


def setup_logger(
    name: str = "llmXive",
    level: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    use_json: bool = False,
) -> logging.Logger:
    """
    Configure and return a logger with structured output.

    Args:
        name: Logger name (default: "llmXive").
        level: Logging level (default: from config or "INFO").
        log_file: Path to log file. If None, logs to stdout/stderr.
        use_json: If True, output logs as JSON lines.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or DEFAULT_LOG_LEVEL))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Determine level from config if not provided
    if level is None:
        config = load_config()
        level = config.get("logging", {}).get("level", DEFAULT_LOG_LEVEL)
        logger.setLevel(getattr(logging, level))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))

    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMATTER))

    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = get_project_root()
            log_path = project_root / log_file

        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, level))

        if use_json:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(LOG_FORMATTER))

        logger.addHandler(file_handler)

    return logger


def log_progress(
    logger: logging.Logger,
    task_name: str,
    current: int,
    total: int,
    message: Optional[str] = None,
    level: str = "INFO",
) -> None:
    """
    Log progress for a long-running task.

    Args:
        logger: Logger instance.
        task_name: Name of the task.
        current: Current progress value.
        total: Total expected value.
        message: Optional custom message.
        level: Logging level (default: "INFO").
    """
    if total <= 0:
        return

    percent = (current / total) * 100
    if percent % PROGRESS_INTERVAL == 0 or percent == 100:
        log_data = {
            "task": task_name,
            "current": current,
            "total": total,
            "percent": f"{percent:.1f}%",
        }
        if message:
            log_data["message"] = message

        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"Progress: {task_name} - {percent:.1f}%", extra={"extra_json": log_data})


def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Union[int, float],
    unit: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a numeric metric with optional context.

    Args:
        logger: Logger instance.
        metric_name: Name of the metric.
        value: Metric value.
        unit: Optional unit (e.g., "eV", "samples").
        context: Optional additional context dictionary.
    """
    log_data = {
        "metric": metric_name,
        "value": value,
        "unit": unit,
    }
    if context:
        log_data["context"] = context

    logger.info(f"Metric: {metric_name} = {value}", extra={"extra_json": log_data})


def log_error_summary(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a structured error summary.

    Args:
        logger: Logger instance.
        error: Exception instance.
        context: Optional additional context.
    """
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if context:
        log_data["context"] = context

    logger.error(f"Error: {type(error).__name__}: {str(error)}", extra={"extra_json": log_data})


# Default logger instance for convenience
_default_logger: Optional[logging.Logger] = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create the default logger.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger(name)
    return _default_logger
