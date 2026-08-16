"""
Logging infrastructure for the Visual Salience on Moral Judgments project.

This module configures a centralized logging system that writes to both
console (stdout) and a project-specific log file. It ensures consistent
formatting, timestamping, and log levels across all pipeline components.

Usage:
    import logging
    from logging_config import setup_logging, get_logger

    # Initialize once at application start
    logger = setup_logging()

    # Or get a named logger for a specific module
    logger = get_logger('data_prep')
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/)
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Standard log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level
DEFAULT_LEVEL = logging.INFO

# Singleton to prevent reconfiguration
_initialized = False


def setup_logging(level: int = DEFAULT_LEVEL, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure the root logger with console and file handlers.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional custom path for the log file. Defaults to LOG_FILE.

    Returns:
        The configured root logger.
    """
    global _initialized
    if _initialized:
        return logging.getLogger()

    if log_file is None:
        log_file = LOG_FILE

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    # File Handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _initialized = True
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with a specific name.

    If the root logger has not been initialized, this will implicitly
    initialize it with default settings to ensure logging works immediately.

    Args:
        name: The name of the logger (usually __name__ of the calling module).

    Returns:
        A configured logger instance.
    """
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)


def set_level(level: int) -> None:
    """
    Dynamically update the log level for all handlers.

    Args:
        level: The new logging level.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


# Initialize immediately on import for convenience
# This ensures that if a module does `from logging_config import get_logger`
# and calls it, the system is ready.
_root = setup_logging()

# Convenience export
logger = _root