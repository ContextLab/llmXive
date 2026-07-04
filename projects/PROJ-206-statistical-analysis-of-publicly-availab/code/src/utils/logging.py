"""
Logging infrastructure for the llmXive statistical analysis pipeline.

Provides a centralized logging configuration that ensures consistent
formatting, log levels, and file output across all pipeline components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Singleton pattern to ensure single configuration instance
_logger_initialized = False
_root_logger: Optional[logging.Logger] = None


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    If the root logger hasn't been configured yet, this function will
    configure it with default settings.

    Args:
        name: The name for the logger (typically __name__ of the module)

    Returns:
        A configured Logger instance
    """
    global _logger_initialized, _root_logger

    if not _logger_initialized:
        configure_logging()

    return logging.getLogger(name)


def configure_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    project_root: Optional[str] = None
) -> None:
    """
    Configure the root logger with the specified settings.

    This function sets up:
    - Console handler with colored output (if supported)
    - Optional file handler for persistent logging
    - Consistent formatting across all handlers

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If None, no file handler is created.
        log_format: Format string for log messages
        date_format: Format string for timestamps
        project_root: Optional path to the project root. Used to resolve relative
                     log file paths. If None, uses current working directory.
    """
    global _logger_initialized, _root_logger

    # Prevent reconfiguration
    if _logger_initialized:
        return

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format, date_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Resolve path relative to project root if provided
        if project_root:
            log_path = Path(project_root) / log_file
        else:
            log_path = Path(log_file)

        # Ensure the directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _logger_initialized = True
    _root_logger = root_logger


def get_log_file_path(log_file: str, project_root: Optional[str] = None) -> Path:
    """
    Resolve the absolute path for a log file.

    Args:
        log_file: The log file path (can be relative or absolute)
        project_root: Optional project root directory

    Returns:
        The resolved absolute Path
    """
    if project_root:
        return Path(project_root) / log_file
    return Path(log_file).resolve()


# Convenience functions for common log levels
def debug(msg: str, logger_name: Optional[str] = None) -> None:
    """Log a debug message."""
    logger = get_logger(logger_name or __name__)
    logger.debug(msg)


def info(msg: str, logger_name: Optional[str] = None) -> None:
    """Log an info message."""
    logger = get_logger(logger_name or __name__)
    logger.info(msg)


def warning(msg: str, logger_name: Optional[str] = None) -> None:
    """Log a warning message."""
    logger = get_logger(logger_name or __name__)
    logger.warning(msg)


def error(msg: str, logger_name: Optional[str] = None) -> None:
    """Log an error message."""
    logger = get_logger(logger_name or __name__)
    logger.error(msg)


def critical(msg: str, logger_name: Optional[str] = None) -> None:
    """Log a critical message."""
    logger = get_logger(logger_name or __name__)
    logger.critical(msg)