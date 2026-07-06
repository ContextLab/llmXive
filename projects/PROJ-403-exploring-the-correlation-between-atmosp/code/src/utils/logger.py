"""
Logging configuration and utilities for the llmXive automated science pipeline.

This module provides a standardized logging setup that respects the project's
configuration (log level, file paths) and ensures consistent formatting across
all components.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Default log configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DIR = "logs"

# Global logger registry to prevent re-configuration
_loggers_configured = set()


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    Configure the root logger and project-wide logging behavior.

    Args:
        log_level: Log level string (e.g., 'DEBUG', 'INFO', 'WARNING').
        log_dir: Directory to store log files. Defaults to 'logs'.
        log_file: Specific log filename. Defaults to 'pipeline.log'.
        enable_console: Whether to log to stdout/stderr.
        enable_file: Whether to log to a file.
    """
    # Load defaults if not provided
    level_str = log_level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_directory = Path(log_dir or os.getenv("LOG_DIR", DEFAULT_LOG_DIR))
    log_filename = log_file or os.getenv("LOG_FILE", "pipeline.log")

    # Ensure log directory exists
    log_directory.mkdir(parents=True, exist_ok=True)

    log_path = log_directory / log_filename

    # Parse level
    try:
        level = getattr(logging, level_str, logging.INFO)
    except AttributeError:
        level = logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if enable_file:
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Mark as configured for this process
    _loggers_configured.add("root")


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, ensuring it is configured according to project standards.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # If the root logger hasn't been explicitly configured yet, do it now
    if "root" not in _loggers_configured:
        setup_logging()

    return logger
