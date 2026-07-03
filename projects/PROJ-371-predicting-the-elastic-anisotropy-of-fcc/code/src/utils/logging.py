"""
Structured logging and error tracking utilities for the llmXive pipeline.
Provides a centralized logging configuration that outputs JSON-formatted logs
for structured analysis and error tracking.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Any, Dict
import traceback

from .config import get_path, get_config

# Global logger instance
_logger: Optional[logging.Logger] = None


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def setup_logger(
    name: str = "llmXive",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    include_console: bool = True,
) -> logging.Logger:
    """
    Configure and return a structured logger.

    Args:
        name: Logger name (default: "llmXive")
        level: Logging level (default: INFO)
        log_file: Optional path to log file. If None, logs only to console.
        include_console: If True, also logs to stdout.

    Returns:
        Configured logging.Logger instance.
    """
    global _logger

    if _logger is not None and _logger.name == name:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    json_formatter = JsonFormatter()

    # Console handler (optional)
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(json_formatter)
        logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_path = get_path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get the configured logger instance.

    Args:
        name: Logger name (default: "llmXive")

    Returns:
        logging.Logger instance.
    """
    global _logger
    if _logger is None:
        # Initialize with defaults if not explicitly set up
        return setup_logger(name=name)
    return _logger


def log_error(
    message: str,
    error: Optional[Exception] = None,
    extra: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive",
) -> None:
    """
    Log an error message with optional exception and extra data.

    Args:
        message: Error message
        error: Optional exception instance to include traceback
        extra: Optional dictionary of additional data to log
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    
    log_record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        "",
        0,
        message,
        (),
        None,
    )
    
    if extra:
        log_record.extra_data = extra
    
    if error:
        log_record.exc_info = (type(error), error, error.__traceback__)
    
    logger.handle(log_record)


def log_warning(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive",
) -> None:
    """Log a warning message with optional extra data."""
    logger = get_logger(logger_name)
    if extra:
        logger.warning(message, extra={"extra_data": extra})
    else:
        logger.warning(message)


def log_info(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive",
) -> None:
    """Log an info message with optional extra data."""
    logger = get_logger(logger_name)
    if extra:
        logger.info(message, extra={"extra_data": extra})
    else:
        logger.info(message)


def log_debug(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive",
) -> None:
    """Log a debug message with optional extra data."""
    logger = get_logger(logger_name)
    if extra:
        logger.debug(message, extra={"extra_data": extra})
    else:
        logger.debug(message)


def log_success(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive",
) -> None:
    """Log a success message (INFO level with success indicator)."""
    logger = get_logger(logger_name)
    success_message = f"[SUCCESS] {message}"
    if extra:
        logger.info(success_message, extra={"extra_data": extra})
    else:
        logger.info(success_message)
