"""
Logging utility for the project.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None
_logging_setup: bool = False

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file
        project_root: Optional project root directory

    Returns:
        Configured logger instance
    """
    global _logger, _logging_setup

    if _logging_setup:
        return _logger

    _logger = logging.getLogger("llmxive")
    _logger.setLevel(level)

    # Clear existing handlers
    _logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        _logger.addHandler(file_handler)

    _logging_setup = True
    return _logger

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    if _logger is None:
        setup_logging()
    return logging.getLogger(name) if name != "llmxive" else _logger

def reset_logging() -> None:
    """Reset logging configuration."""
    global _logger, _logging_setup
    _logger = None
    _logging_setup = False

def debug(msg: str) -> None:
    """Log debug message."""
    if _logger:
        _logger.debug(msg)

def info(msg: str) -> None:
    """Log info message."""
    if _logger:
        _logger.info(msg)

def warning(msg: str) -> None:
    """Log warning message."""
    if _logger:
        _logger.warning(msg)

def error(msg: str) -> None:
    """Log error message."""
    if _logger:
        _logger.error(msg)

def critical(msg: str) -> None:
    """Log critical message."""
    if _logger:
        _logger.critical(msg)

def exception(msg: str, exc_info: bool = True) -> None:
    """Log exception with traceback."""
    if _logger:
        _logger.exception(msg, exc_info=exc_info)
