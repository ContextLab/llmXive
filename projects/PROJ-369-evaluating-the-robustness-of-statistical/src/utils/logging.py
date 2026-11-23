"""
Structured logging utilities for the llmXive research pipeline.

Provides a consistent logging interface with JSON formatting,
file rotation, and level-specific helper functions.
"""

import logging
import json
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from logging.handlers import RotatingFileHandler

from src.utils.config import get_path


class StructuredFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs JSON-structured logs.
    
    Includes timestamp, level, logger name, message, and optional
    extra context fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add standard attributes if present
        if hasattr(record, "module"):
            log_data["module"] = record.module
        if hasattr(record, "lineno"):
            log_data["lineno"] = record.lineno
        if hasattr(record, "funcName"):
            log_data["function"] = record.funcName

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra context if available
        if hasattr(record, "extra_data") and record.extra_data:
            log_data["context"] = record.extra_data

        return json.dumps(log_data)


def setup_logger(
    name: str = "llmXive",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure and return a logger with structured JSON formatting.

    Args:
        name: Logger name.
        log_level: Minimum log level (e.g., logging.INFO, logging.DEBUG).
        log_file: Relative path to log file (relative to project root).
                  If None, logs only to stderr.
        max_bytes: Max size per log file before rotation.
        backup_count: Number of backup files to keep.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    formatter = StructuredFormatter()

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation if log_file is provided
    if log_file:
        log_path = get_path(log_file)
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve an existing logger or create a new one with default settings.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


def _log_with_level(
    level: int,
    message: str,
    logger_name: str = "llmXive",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Internal helper to log a message at a specific level with optional context.

    Args:
        level: Logging level (e.g., logging.INFO).
        message: Log message.
        logger_name: Logger name.
        extra_data: Optional dictionary of contextual data.
    """
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None,
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)


def log_info(
    message: str,
    logger_name: str = "llmXive",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an informational message."""
    _log_with_level(logging.INFO, message, logger_name, extra_data)


def log_warning(
    message: str,
    logger_name: str = "llmXive",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a warning message."""
    _log_with_level(logging.WARNING, message, logger_name, extra_data)


def log_error(
    message: str,
    logger_name: str = "llmXive",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an error message."""
    _log_with_level(logging.ERROR, message, logger_name, extra_data)


def log_critical(
    message: str,
    logger_name: str = "llmXive",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a critical message."""
    _log_with_level(logging.CRITICAL, message, logger_name, extra_data)


def log_debug(
    message: str,
    logger_name: str = "llmXive",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a debug message."""
    _log_with_level(logging.DEBUG, message, logger_name, extra_data)