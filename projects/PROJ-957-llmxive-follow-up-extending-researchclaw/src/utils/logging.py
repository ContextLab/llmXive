"""
Structured JSON logging and error tracking for llmXive.

Provides a centralized logging configuration that outputs JSON-formatted
logs to stdout and files, with automatic error tracking and context enrichment.
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Constants
LOG_DIR = Path("logs")
LOG_FILE_NAME = "experiment.log"
ERROR_LOG_FILE_NAME = "errors.log"

# Global logger instance
_logger: Optional[logging.Logger] = None
_initialized: bool = False


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON with enriched context."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "experiment_id"):
            log_data["experiment_id"] = record.experiment_id
        if hasattr(record, "stage"):
            log_data["stage"] = record.stage

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data)


def _ensure_log_dir() -> None:
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get or create a configured logger instance.

    Args:
        name: Logger name (default: "llmxive")

    Returns:
        Configured logger instance
    """
    global _logger, _initialized

    if not _initialized:
        setup_logging()

    return logging.getLogger(name)


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: Optional[Path] = None,
) -> None:
    """
    Configure the root logger with JSON formatting and file handlers.

    Args:
        level: Logging level (default: INFO)
        log_to_file: Whether to write logs to file (default: True)
        log_to_console: Whether to print logs to console (default: True)
        log_dir: Directory for log files (default: logs/)
    """
    global _logger, _initialized

    if _initialized:
        return

    _log_dir = log_dir if log_dir else LOG_DIR
    _ensure_log_dir()

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    json_formatter = JsonFormatter()

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    # File handler for general logs
    if log_to_file:
        log_file_path = _log_dir / LOG_FILE_NAME
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

        # Error-specific file handler (ERROR and above)
        error_log_path = _log_dir / ERROR_LOG_FILE_NAME
        error_handler = logging.FileHandler(error_log_path, encoding="utf-8")
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)

    _initialized = True


def log_error(
    message: str,
    exception: Optional[Exception] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    task_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    stage: Optional[str] = None,
) -> None:
    """
    Log an error message with optional exception details and context.

    Args:
        message: Error message
        exception: Optional exception instance to log
        extra_context: Additional context to include in the log
        task_id: Associated task ID
        experiment_id: Associated experiment ID
        stage: Current stage of execution
    """
    logger = get_logger()

    extra: Dict[str, Any] = {}
    if task_id:
        extra["task_id"] = task_id
    if experiment_id:
        extra["experiment_id"] = experiment_id
    if stage:
        extra["stage"] = stage
    if extra_context:
        extra.update(extra_context)

    if exception:
        logger.error(
            message,
            exc_info=True,
            extra=extra,
        )
    else:
        logger.error(message, extra=extra)


def log_info(
    message: str,
    task_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    stage: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log an informational message with optional context.

    Args:
        message: Log message
        task_id: Associated task ID
        experiment_id: Associated experiment ID
        stage: Current stage of execution
        **kwargs: Additional context fields
    """
    logger = get_logger()
    extra: Dict[str, Any] = {}
    if task_id:
        extra["task_id"] = task_id
    if experiment_id:
        extra["experiment_id"] = experiment_id
    if stage:
        extra["stage"] = stage
    extra.update(kwargs)

    logger.info(message, extra=extra)


def log_warning(
    message: str,
    task_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    stage: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log a warning message with optional context.

    Args:
        message: Warning message
        task_id: Associated task ID
        experiment_id: Associated experiment ID
        stage: Current stage of execution
        **kwargs: Additional context fields
    """
    logger = get_logger()
    extra: Dict[str, Any] = {}
    if task_id:
        extra["task_id"] = task_id
    if experiment_id:
        extra["experiment_id"] = experiment_id
    if stage:
        extra["stage"] = stage
    extra.update(kwargs)

    logger.warning(message, extra=extra)


def log_debug(
    message: str,
    task_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    stage: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log a debug message with optional context.

    Args:
        message: Debug message
        task_id: Associated task ID
        experiment_id: Associated experiment ID
        stage: Current stage of execution
        **kwargs: Additional context fields
    """
    logger = get_logger()
    extra: Dict[str, Any] = {}
    if task_id:
        extra["task_id"] = task_id
    if experiment_id:
        extra["experiment_id"] = experiment_id
    if stage:
        extra["stage"] = stage
    extra.update(kwargs)

    logger.debug(message, extra=extra)


def read_logs(
    num_lines: Optional[int] = None,
    level: Optional[str] = None,
    task_id: Optional[str] = None,
) -> list[str]:
    """
    Read log entries from the latest log file.

    Args:
        num_lines: Number of lines to read (None for all)
        level: Filter by log level (e.g., "ERROR", "WARNING")
        task_id: Filter by task ID

    Returns:
        List of log entries (as JSON strings)
    """
    log_file = LOG_DIR / LOG_FILE_NAME
    if not log_file.exists():
        return []

    entries = []
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if num_lines:
        lines = lines[-num_lines:]

    for line in lines:
        try:
            entry = json.loads(line.strip())
            # Apply filters
            if level and entry.get("level") != level:
                continue
            if task_id and entry.get("task_id") != task_id:
                continue
            entries.append(line.strip())
        except json.JSONDecodeError:
            continue

    return entries


def read_errors(
    num_lines: Optional[int] = None,
) -> list[str]:
    """
    Read error log entries from the error log file.

    Args:
        num_lines: Number of lines to read (None for all)

    Returns:
        List of error log entries
    """
    error_file = LOG_DIR / ERROR_LOG_FILE_NAME
    if not error_file.exists():
        return []

    entries = []
    with open(error_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if num_lines:
        lines = lines[-num_lines:]

    entries.extend(line.strip() for line in lines)
    return entries