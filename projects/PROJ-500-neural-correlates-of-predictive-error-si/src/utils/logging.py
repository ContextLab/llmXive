"""
Structured logging utility for the llmXive pipeline.

Provides a singleton logger configuration that outputs JSON-formatted logs
to both a file (under data/logs/) and stdout, ensuring pipeline traceability.
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import the config singleton to ensure consistent paths
from .config import Config

_logger_instance: Optional[logging.Logger] = None
_lock = threading.Lock()

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
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
        if hasattr(record, "subject_id"):
            log_data["subject_id"] = record.subject_id
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def get_logger(task_id: Optional[str] = None) -> logging.Logger:
    """
    Returns a configured singleton logger instance.

    Args:
        task_id: Optional task identifier to attach to all log records.

    Returns:
        A logging.Logger instance configured for JSON output.
    """
    global _logger_instance

    if _logger_instance is None:
        with _lock:
            if _logger_instance is None:
                _init_logger(task_id)

    return _logger_instance

def _init_logger(task_id: Optional[str] = None) -> None:
    """
    Initializes the logger with JSON formatting and file handlers.

    Args:
        task_id: Optional task identifier to attach to all log records.
    """
    global _logger_instance

    config = Config.get_instance()
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler (pipeline traceability)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.jsonl"
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    _logger_instance = logger

    if task_id:
        # We attach the task_id to the logger's extra context via a filter
        # rather than modifying the logger name, to keep it generic but traceable.
        class TaskIdFilter(logging.Filter):
            def __init__(self, tid: str):
                super().__init__()
                self.tid = tid

            def filter(self, record: logging.LogRecord) -> bool:
                record.task_id = self.tid
                return True

        logger.addFilter(TaskIdFilter(task_id))

def log_event(
    message: str,
    level: str = "INFO",
    task_id: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Convenience function to log an event with optional extra fields.

    Args:
        message: The log message.
        level: Log level string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        task_id: Optional task ID to override the default.
        **extra_fields: Additional key-value pairs to include in the JSON log.
    """
    logger = get_logger(task_id)
    log_method = getattr(logger, level.lower(), logger.info)

    # Create a record with extra fields attached
    # We use a custom LogRecord to inject extra fields
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level),
        "",
        0,
        message,
        (),
        None
    )

    # Attach extra fields
    for key, value in extra_fields.items():
        setattr(record, key, value)

    logger.handle(record)

def log_error(
    message: str,
    error_code: Optional[str] = None,
    task_id: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Logs an error with optional error code and extra context.

    Args:
        message: The error message.
        error_code: Optional error code string.
        task_id: Optional task ID.
        **extra_fields: Additional context fields.
    """
    logger = get_logger(task_id)
    record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        "",
        0,
        message,
        (),
        None
    )

    if error_code:
        setattr(record, "error_code", error_code)

    for key, value in extra_fields.items():
        setattr(record, key, value)

    logger.handle(record)

def log_progress(
    message: str,
    task_id: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Logs a progress update (INFO level).

    Args:
        message: Progress message.
        task_id: Optional task ID.
        **extra_fields: Additional context fields.
    """
    log_event(message, level="INFO", task_id=task_id, **extra_fields)

def log_debug(
    message: str,
    task_id: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Logs a debug message.

    Args:
        message: Debug message.
        task_id: Optional task ID.
        **extra_fields: Additional context fields.
    """
    log_event(message, level="DEBUG", task_id=task_id, **extra_fields)

def log_warning(
    message: str,
    task_id: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Logs a warning message.

    Args:
        message: Warning message.
        task_id: Optional task ID.
        **extra_fields: Additional context fields.
    """
    log_event(message, level="WARNING", task_id=task_id, **extra_fields)

def log_critical(
    message: str,
    task_id: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Logs a critical message.

    Args:
        message: Critical message.
        task_id: Optional task ID.
        **extra_fields: Additional context fields.
    """
    log_event(message, level="CRITICAL", task_id=task_id, **extra_fields)
