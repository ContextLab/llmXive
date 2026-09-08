"""
Structured logging and progress tracking utilities for the llmXive pipeline.

This module provides a consistent logging configuration across the project,
ensuring structured JSON logs for machine parsing and human-readable logs
for terminal output. It also includes progress tracking utilities for long-running
data ingestion and processing tasks.
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from logging.handlers import RotatingFileHandler
import os

# Constants
LOG_DIR = Path("data/logs")
DEFAULT_LOG_FILE = "pipeline.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5
LOG_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    enable_json: bool = False,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure the root logger with structured logging capabilities.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses default data/logs/pipeline.log
        enable_json: If True, log file output will be JSON formatted
        console_output: If True, logs are also sent to console

    Returns:
        Configured root logger
    """
    # Ensure log directory exists
    log_path = Path(log_file) if log_file else LOG_DIR / DEFAULT_LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    if enable_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(LOG_FORMATTER)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()


def log_progress(
    logger: logging.Logger,
    task_name: str,
    current: int,
    total: int,
    message: Optional[str] = None,
    level: str = "INFO",
) -> None:
    """
    Log progress of a long-running task with percentage completion.

    Args:
        logger: Logger instance to use
        task_name: Name of the task being tracked
        current: Current progress count
        total: Total expected count
        message: Optional additional message
        level: Log level (default: INFO)
    """
    if total <= 0:
        percentage = 0.0
    else:
        percentage = (current / total) * 100

    status_msg = f"Progress: {task_name} - {current:,}/{total:,} ({percentage:.1f}%)"
    if message:
        status_msg += f" - {message}"

    log_func = getattr(logger, level.lower(), logger.info)
    log_func(status_msg, extra={"extra_data": {
        "task": task_name,
        "current": current,
        "total": total,
        "percentage": round(percentage, 2),
    }})


def log_stage_start(logger: logging.Logger, stage_name: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of a pipeline stage.

    Args:
        logger: Logger instance
        stage_name: Name of the stage
        details: Optional dictionary of stage details/metadata
    """
    msg = f"=== STARTING STAGE: {stage_name} ==="
    extra_data = {"stage": stage_name, "event": "start"}
    if details:
        extra_data.update(details)

    logger.info(msg, extra={"extra_data": extra_data})


def log_stage_end(
    logger: logging.Logger,
    stage_name: str,
    success: bool = True,
    duration_seconds: Optional[float] = None,
    metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log the end of a pipeline stage.

    Args:
        logger: Logger instance
        stage_name: Name of the stage
        success: Whether the stage completed successfully
        duration_seconds: Duration of the stage in seconds
        metrics: Optional dictionary of metrics collected during the stage
    """
    status = "SUCCESS" if success else "FAILED"
    msg = f"=== COMPLETED STAGE: {stage_name} [{status}] ==="
    extra_data = {"stage": stage_name, "event": "end", "success": success}

    if duration_seconds is not None:
        extra_data["duration_seconds"] = duration_seconds
        msg += f" (Duration: {duration_seconds:.2f}s)"

    if metrics:
        extra_data["metrics"] = metrics
        msg += f" - Metrics: {metrics}"

    log_level = "info" if success else "error"
    log_func = getattr(logger, log_level, logger.error)
    log_func(msg, extra={"extra_data": extra_data})


def log_error_context(
    logger: logging.Logger,
    error_msg: str,
    context: Dict[str, Any],
    exc_info: bool = False,
) -> None:
    """
    Log an error with additional context information.

    Args:
        logger: Logger instance
        error_msg: Error message
        context: Dictionary of context information (e.g., file paths, IDs, parameters)
        exc_info: Whether to include exception traceback
    """
    msg = f"ERROR: {error_msg}"
    extra_data = {"error": error_msg, "context": context}

    logger.error(msg, extra={"extra_data": extra_data}, exc_info=exc_info)
