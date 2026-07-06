"""
Logging infrastructure for the rotating BEC simulation pipeline.

Provides a centralized logging configuration that ensures consistent
formatting, log levels, and file output for all simulation, analysis,
and statistics components.

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Simulation started")
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

# Project root relative to this file (code/utils/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default log configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log directory path
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE_NAME = "simulation_run.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global configuration flag to prevent re-initialization
_logging_configured = False


def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Union[str, Path]] = None,
    console_output: bool = True,
    file_output: bool = True,
) -> None:
    """
    Configure the root logger with specified handlers and formatting.

    This function sets up:
    - A file handler writing to the logs directory
    - A console handler for stdout/stderr
    - Consistent formatting for both handlers

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path for log file. If None, uses default.
        console_output: If True, add a StreamHandler for console output.
        file_output: If True, add a FileHandler for file output.
    """
    global _logging_configured

    if _logging_configured:
        return

    # Determine log file path
    if log_file is None:
        log_path = LOG_DIR / LOG_FILE_NAME
    else:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path

    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DATE_FORMAT
    )

    # Add file handler
    if file_output:
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    This ensures the logger inherits the configuration set by
    configure_logging(). If logging hasn't been configured yet,
    it will be configured with default settings.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    # Auto-configure if not already done
    if not _logging_configured:
        configure_logging()

    return logging.getLogger(name)


def get_log_file_path() -> Path:
    """
    Get the current log file path.

    Returns:
        Path object pointing to the active log file.
    """
    return LOG_DIR / LOG_FILE_NAME


def clear_handlers() -> None:
    """
    Remove all handlers from the root logger.

    Useful for testing or reconfiguring logging dynamically.
    """
    global _logging_configured
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    _logging_configured = False


# Convenience functions for common log levels
def debug(msg: str, *args, **kwargs) -> None:
    """Log a debug message using the default logger."""
    logging.getLogger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Log an info message using the default logger."""
    logging.getLogger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log a warning message using the default logger."""
    logging.getLogger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log an error message using the default logger."""
    logging.getLogger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """Log a critical message using the default logger."""
    logging.getLogger().critical(msg, *args, **kwargs)


# Initialize default configuration on module import
# This ensures logging is available immediately without explicit setup
configure_logging()