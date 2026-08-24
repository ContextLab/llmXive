"""
Base logging infrastructure with structured JSON output for llmXive.

This module provides a centralized logging configuration that outputs
structured JSON logs suitable for automated parsing and analysis.
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# Project-specific constants
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "llmxive.log")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Global logger instance
_logger: Optional[logging.Logger] = None


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create the project logger with JSON formatting.

    Args:
        name: Optional name for the logger. If None, uses 'llmxive'.

    Returns:
        Configured logger instance.
    """
    global _logger

    logger_name = name if name else "llmxive"

    # Return cached logger if already configured
    if _logger and _logger.name == logger_name:
        return _logger

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JsonFormatter())

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Cache the logger
    _logger = logger

    return logger


def log_event(
    level: int,
    message: str,
    logger_name: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Log an event with optional extra fields.

    Args:
        level: Logging level (e.g., logging.INFO, logging.ERROR).
        message: Log message.
        logger_name: Optional logger name.
        **extra_fields: Additional fields to include in the JSON log.
    """
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.extra_data = extra_fields
    logger.handle(record)


def log_info(message: str, logger_name: Optional[str] = None, **extra_fields: Any) -> None:
    """Log an info-level message."""
    log_event(logging.INFO, message, logger_name, **extra_fields)


def log_warning(message: str, logger_name: Optional[str] = None, **extra_fields: Any) -> None:
    """Log a warning-level message."""
    log_event(logging.WARNING, message, logger_name, **extra_fields)


def log_error(message: str, logger_name: Optional[str] = None, **extra_fields: Any) -> None:
    """Log an error-level message."""
    log_event(logging.ERROR, message, logger_name, **extra_fields)


def log_exception(
    message: str,
    exc: Optional[BaseException] = None,
    logger_name: Optional[str] = None,
    **extra_fields: Any
) -> None:
    """
    Log an exception with full traceback.

    Args:
        message: Error message.
        exc: Optional exception instance. If None, uses current exception.
        logger_name: Optional logger name.
        **extra_fields: Additional fields to include in the JSON log.
    """
    logger = get_logger(logger_name)
    if exc:
        logger.exception(message, exc_info=(type(exc), exc, exc.__traceback__), **extra_fields)
    else:
        logger.exception(message, **extra_fields)


def fail_loudly(message: str, error: Optional[BaseException] = None) -> None:
    """
    Log a fatal error and raise an exception.

    This function ensures that critical failures are logged with full
    context before raising an exception, preventing silent failures.

    Args:
        message: Error description.
        error: Optional exception to raise. If None, raises RuntimeError.

    Raises:
        RuntimeError: If no specific exception is provided.
        The provided exception: If one is given.
    """
    if error:
        log_exception(f"FATAL: {message}", error)
        raise error
    else:
        log_error(f"FATAL: {message}")
        raise RuntimeError(message)