"""
Logging infrastructure for the plasma confinement analysis pipeline.

This module provides centralized logging configuration and utility functions
for creating and managing loggers throughout the application. It supports
both console and file output with configurable levels and formatting.

Functions:
    setup_logging: Configure the root logger with console and file handlers.
    get_logger: Retrieve or create a named logger with consistent configuration.

Example:
    >>> from utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Starting analysis...")
"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


# Default log configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_LOG_DIR = Path('logs')
DEFAULT_LOG_FILE = 'pipeline.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup files


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Configure the root logger with console and file handlers.

    This function sets up a comprehensive logging configuration that includes
    both console output (for immediate feedback) and file output (for persistent
    records). The file handler uses rotating file handlers to prevent log files
    from growing indefinitely.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_dir: Directory for log files. Defaults to 'logs' relative to current directory.
        log_file: Name of the log file. Defaults to 'pipeline.log'.
        format_string: Format string for log messages.
        date_format: Date format string for timestamps.
        enable_console: Whether to add a console handler.
        enable_file: Whether to add a file handler.

    Returns:
        The configured root logger.

    Raises:
        OSError: If the log directory cannot be created or accessed.

    Example:
        >>> setup_logging(level=logging.DEBUG, log_dir=Path('custom_logs'))
        >>> logger = logging.getLogger()
        >>> logger.info("Logging is configured")
    """
    # Use defaults if not provided
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_file = log_file or DEFAULT_LOG_FILE
    format_string = format_string or DEFAULT_LOG_FORMAT
    date_format = date_format or DEFAULT_DATE_FORMAT

    # Create log directory if it doesn't exist
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(format_string, date_format)

    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler with rotation
    if enable_file:
        log_path = log_dir / log_file
        try:
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError as e:
            # If file handler fails, at least ensure console logging works
            print(f"Warning: Could not create file handler: {e}", file=sys.stderr)

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a named logger with consistent configuration.

    This function provides a convenient way to get a logger that inherits
    the configuration from the root logger. It is recommended to use this
    function instead of directly calling logging.getLogger() to ensure
    consistent behavior across the application.

    Args:
        name: Name of the logger. Typically __name__ of the calling module.
             If None, returns the root logger.

    Returns:
        A configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
        >>> logger.info("Info message")
        >>> logger.warning("Warning message")
        >>> logger.error("Error message")
        >>> logger.critical("Critical message")
    """
    return logging.getLogger(name)
