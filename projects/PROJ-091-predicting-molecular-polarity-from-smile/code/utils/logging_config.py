"""
Logging infrastructure configuration for the molecular polarity prediction pipeline.

Configures a rotating file handler for logs/app.log with JSON formatting.
"""
import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure log directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Default log level
DEFAULT_LEVEL = logging.INFO

# Singleton logger instance
_logger: Optional[logging.Logger] = None


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        # Include extra context if available
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def get_logger(name: str = "molecular_polarity") -> logging.Logger:
    """
    Retrieve or configure the project logger.

    Args:
        name: Logger name (defaults to project name).

    Returns:
        Configured logger instance.
    """
    global _logger

    if _logger is not None:
        return _logger

    # Create root logger
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LEVEL)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(DEFAULT_LEVEL)
    file_handler.setFormatter(JsonFormatter())

    # Create console handler for immediate feedback during development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(JsonFormatter())

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    _logger = logger
    return logger


def set_log_level(level: int) -> None:
    """
    Update the log level for all handlers.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    """
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def log_with_context(msg: str, context: Dict[str, Any], level: int = logging.INFO) -> None:
    """
    Log a message with additional structured context.

    Args:
        msg: Log message.
        context: Dictionary of additional key-value pairs to include.
        level: Logging level.
    """
    logger = get_logger()
    extra = {"extra_data": context}
    logger.log(level, msg, extra=extra)
