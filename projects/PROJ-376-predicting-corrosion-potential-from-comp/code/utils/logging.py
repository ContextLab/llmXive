"""
Logging infrastructure setup for the corrosion prediction pipeline.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Global logger registry
_loggers = {}
_log_level = logging.INFO


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with optional file and console handlers.

    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file. If None, no file handler is added.
        level: Logging level
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    # Default setup if not explicitly configured
    return setup_logger(name, console=True, level=_log_level)


def log_message(
    logger_name: str,
    message: str,
    level: int = logging.INFO
) -> None:
    """
    Log a message to a specific logger.

    Args:
        logger_name: Name of the logger
        message: Message to log
        level: Logging level
    """
    logger = get_logger(logger_name)
    logger.log(level, message)
