"""
Logging infrastructure for the llmXive project.

Provides a centralized logging configuration that outputs to both
console and file, with appropriate formatting and levels.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_DIR = "data/logs"
DEFAULT_LOG_FILE = "pipeline.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes this file is at code/utils/logger.py relative to root.
    """
    current_file = Path(__file__).resolve()
    # Go up from code/utils/logger.py -> code -> root
    return current_file.parent.parent.parent


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_date_format: str = DEFAULT_LOG_DATE_FORMAT,
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    Configure and return the root logger with handlers.

    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_format: Format string for log messages
        log_date_format: Date format string for log timestamps
        log_dir: Directory to store log files (relative to project root)
        log_file: Name of the log file
        max_bytes: Maximum size of a log file before rotation
        backup_count: Number of backup files to keep
        console: Whether to add a console handler
        file: Whether to add a file handler

    Returns:
        The configured root logger instance.
    """
    project_root = get_project_root()
    log_path = project_root / log_dir

    # Ensure log directory exists
    log_path.mkdir(parents=True, exist_ok=True)

    log_file_path = log_path / log_file

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format, log_date_format)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if file:
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


# Initialize logger on module import if desired, or call setup_logging explicitly
# For explicit control, we do not auto-initialize here.
# Usage:
#   from code.utils.logger import setup_logging, get_logger
#   setup_logging()
#   logger = get_logger(__name__)
#   logger.info("Message")
