"""
Standardized logging configuration for the llmXive research pipeline.

This module provides a consistent logging setup across all project scripts,
ensuring uniform formatting, log levels, and output destinations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_project_root


# Default log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance cache
_loggers: dict = {}


def get_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    propagate: bool = True
) -> logging.Logger:
    """
    Get or create a logger with standardized configuration.

    Args:
        name: Logger name. If None, uses the project root name.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional relative path to a log file within the project root.
        propagate: Whether to propagate logs to parent loggers.

    Returns:
        Configured logging.Logger instance.
    """
    if name is None:
        name = "llmXive"

    # Return cached logger if it exists
    if name in _loggers:
        logger = _loggers[name]
        # Update level if requested
        if level != logger.level:
            logger.setLevel(level)
        return logger

    # Create new logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    # Avoid adding handlers if they already exist
    if logger.handlers:
        _loggers[name] = logger
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        project_root = get_project_root()
        log_path = project_root / log_file
        
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def configure_root_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> None:
    """
    Configure the root logger for the entire application.

    This should be called once at the start of the main entry point.

    Args:
        level: Logging level for the root logger.
        log_file: Optional relative path to a log file within the project root.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        project_root = get_project_root()
        log_path = project_root / log_file
        
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)


def get_log_path(log_file: str) -> Path:
    """
    Resolve a log file path relative to the project root.

    Args:
        log_file: Relative path to the log file.

    Returns:
        Absolute Path object for the log file.
    """
    return get_project_root() / log_file
