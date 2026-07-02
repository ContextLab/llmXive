"""
Logging configuration for the social memory networks project.
Provides setup_logger and get_logger functions.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Global logger instance cache
_loggers: dict[str, logging.Logger] = {}

def setup_logger(
    name: str = "social_memory",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    include_timestamp: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with optional file handler.

    Args:
        name: Logger name
        log_file: Optional path to log file (relative to project root)
        level: Logging level
        include_timestamp: Whether to include timestamps in console output

    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if include_timestamp:
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        console_format = "%(name)s - %(levelname)s - %(message)s"

    console_formatter = logging.Formatter(console_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger

def get_logger(name: str = "social_memory") -> logging.Logger:
    """
    Get a logger by name, creating it if it doesn't exist.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    if name not in _loggers:
        # Create with default settings
        return setup_logger(name)
    return _loggers[name]
