"""
Structured logging infrastructure for the llmXive science pipeline.

This module provides a centralized logging configuration that outputs
structured logs (JSON) to both console and file, with support for
log levels, memory monitoring integration, and task context.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Import existing memory monitor to integrate with logging
from .memory_monitor import get_current_memory_mb, check_memory_limit, MemoryLimitExceeded

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_FILE = "pipeline.log"
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON with structured fields.
    Includes timestamp, level, message, module, function, line number,
    and optional extra context (e.g., memory usage, task_id).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add optional context from extra fields
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id
        if hasattr(record, "memory_mb"):
            log_entry["memory_mb"] = record.memory_mb
        if hasattr(record, "error_type"):
            log_entry["error_type"] = record.error_type

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def _get_logger() -> logging.Logger:
    """
    Get or create the project's main logger.
    Ensures only one handler setup per logger instance.
    """
    logger = logging.getLogger("llmXive")
    if logger.handlers:
        return logger

    logger.setLevel(DEFAULT_LOG_LEVEL)
    logger.propagate = False  # Prevent double logging to root

    # Ensure log directory exists
    log_dir = DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(DEFAULT_LOG_LEVEL)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    # File handler (rotating)
    file_path = log_dir / DEFAULT_LOG_FILE
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Capture all debug info to file
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, returns a child logger.
    """
    parent = _get_logger()
    if name:
        return parent.getChild(name)
    return parent

def log_with_memory(
    level: int,
    message: str,
    logger: Optional[logging.Logger] = None,
    **extra: Any
) -> None:
    """
    Log a message with current memory usage included.

    Args:
        level: Log level (e.g., logging.INFO)
        message: Log message
        logger: Logger instance (defaults to project logger)
        **extra: Additional context fields to include in the log
    """
    if logger is None:
        logger = get_logger()

    # Check memory limit before logging critical operations
    try:
        check_memory_limit()
    except MemoryLimitExceeded:
        # Log the memory exceeded event at ERROR level
        logger.error(
            "Memory limit exceeded during operation.",
            extra={"memory_mb": get_current_memory_mb(), "error_type": "MemoryLimitExceeded", **extra}
        )
        raise

    # Add memory to context
    extra["memory_mb"] = get_current_memory_mb()
    logger.log(level, message, extra=extra)

def configure_logger(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Union[str, Path] = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
) -> logging.Logger:
    """
    Re-configure the logging infrastructure with custom settings.
    Useful for different environments (e.g., debug vs production).

    Args:
        log_level: Minimum log level to display
        log_dir: Directory for log files
        log_file: Name of the log file
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Clear existing handlers to re-configure
    logger = logging.getLogger("llmXive")
    logger.handlers.clear()
    logger.setLevel(log_level)
    logger.propagate = False

    # Update global defaults for this session
    global DEFAULT_LOG_DIR, DEFAULT_LOG_FILE, MAX_BYTES, BACKUP_COUNT
    DEFAULT_LOG_DIR = Path(log_dir)
    DEFAULT_LOG_FILE = log_file
    MAX_BYTES = max_bytes
    BACKUP_COUNT = backup_count

    # Ensure directory exists
    DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    # File handler
    file_path = DEFAULT_LOG_DIR / DEFAULT_LOG_FILE
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    return logger

# Initialize default logger on module import
_default_logger = _get_logger()