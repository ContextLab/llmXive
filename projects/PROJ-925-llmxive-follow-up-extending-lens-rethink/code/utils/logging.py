"""
Logging infrastructure for the llmXive research pipeline.

Provides a centralized logging configuration and utility functions
to ensure consistent log formatting, file rotation, and log levels
across all project modules.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Project root is assumed to be two levels up from this file
# code/utils/logging.py -> code/utils -> code -> root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"
_LOG_FILE = _LOG_DIR / "pipeline.log"

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

_configured = False
_root_logger: Optional[logging.Logger] = None


def _ensure_log_dir() -> None:
    """Create the log directory if it does not exist."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the log file. Defaults to data/logs/pipeline.log.
        console: Whether to also log to stdout/stderr.

    Returns:
        The configured root logger.
    """
    global _configured, _root_logger

    if _configured:
        return _root_logger

    _ensure_log_dir()
    target_log_file = log_file or _LOG_FILE

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-runs in same process
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # File Handler (Rotating)
    try:
        file_handler = RotatingFileHandler(
            target_log_file,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file cannot be opened (e.g., permissions)
        logging.warning(f"Failed to initialize file logging: {e}")

    # Console Handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _configured = True
    _root_logger = root_logger

    # Log startup info
    root_logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
    root_logger.info(f"Log file: {target_log_file}")

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    If the root logger has not been configured yet, this function
    will attempt to configure it with default settings first.

    Args:
        name: The name of the logger (e.g., 'code.features').
            If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    if not _configured:
        setup_logging()

    if name is None:
        return _root_logger

    return logging.getLogger(name)


def log_exception(msg: str, exc_info: bool = True) -> None:
    """
    Log an exception at the ERROR level.

    Args:
        msg: The error message.
        exc_info: Whether to include exception traceback.
    """
    logger = get_logger()
    logger.error(msg, exc_info=exc_info)


def log_critical(msg: str) -> None:
    """Log a critical message."""
    get_logger().critical(msg)


def log_warning(msg: str) -> None:
    """Log a warning message."""
    get_logger().warning(msg)


def log_info(msg: str) -> None:
    """Log an info message."""
    get_logger().info(msg)


def log_debug(msg: str) -> None:
    """Log a debug message."""
    get_logger().debug(msg)
