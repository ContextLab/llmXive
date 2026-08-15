"""
Logging infrastructure for the sensitivity analysis pipeline.

Provides structured JSON logging to artifacts/run.log and console output.
Ensures all log records include timestamps, log levels, and execution context.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# Constants
LOG_DIR = "artifacts"
LOG_FILE = os.path.join(LOG_DIR, "run.log")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Global logger instance
_logger: Optional[logging.Logger] = None


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_logger(name: str = "sensitivity_pipeline") -> logging.Logger:
    """
    Returns a configured logger instance.

    Args:
        name: Name for the logger (default: "sensitivity_pipeline")

    Returns:
        Configured logger instance with JSON file handler and console handler.
    """
    global _logger

    if _logger is not None and _logger.name == name:
        return _logger

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a message with optional structured context data.

    Args:
        logger: Logger instance to use
        level: Logging level (e.g., logging.INFO, logging.ERROR)
        message: Log message string
        context: Optional dictionary of additional context data
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None,
    )
    if context:
        record.extra_data = context
    logger.handle(record)


def setup_logging() -> logging.Logger:
    """
    Initialize the global logging infrastructure.

    Returns:
        The configured global logger instance.
    """
    return get_logger()


# Convenience functions for quick logging
def info(msg: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an info message with optional context."""
    logger = get_logger()
    log_with_context(logger, logging.INFO, msg, context)


def debug(msg: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a debug message with optional context."""
    logger = get_logger()
    log_with_context(logger, logging.DEBUG, msg, context)


def warning(msg: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a warning message with optional context."""
    logger = get_logger()
    log_with_context(logger, logging.WARNING, msg, context)


def error(msg: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
    """Log an error message with optional context and exception info."""
    logger = get_logger()
    if exc_info:
        logger.error(msg, extra={"extra_data": context} if context else {})
    else:
        log_with_context(logger, logging.ERROR, msg, context)


def critical(msg: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a critical message with optional context."""
    logger = get_logger()
    log_with_context(logger, logging.CRITICAL, msg, context)
