"""
Logging infrastructure setup for the corrosion prediction pipeline.
Implements FR-010: Reproducible logging with timestamps, levels, and structured output.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Global logger registry to prevent duplicate handlers
_loggers = {}
_log_level = logging.INFO

# Default log directory (relative to project root)
# This aligns with T001 setup: data/logs/
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_FILE = "pipeline.log"


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with optional file and console handlers.
    Ensures reproducible formatting and prevents duplicate handlers.

    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file relative to project root. If None, no file handler is added.
        level: Logging level
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    # Use absolute path if relative is provided, resolving from project root
    if log_file and not os.path.isabs(log_file):
        # Ensure log directory exists
        log_path = Path(log_file)
        if not log_path.is_absolute():
            # Assume relative to project root
            full_log_path = Path.cwd() / log_file
        else:
            full_log_path = log_path
        
        # Create parent directories if they don't exist
        full_log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        full_log_path = None

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Remove existing handlers to avoid duplicates during re-runs
    logger.handlers.clear()

    # Reproducible formatter with ISO timestamp
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
    if full_log_path:
        fh = logging.FileHandler(str(full_log_path))
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    Default settings include file logging to data/logs/pipeline.log.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    # Default setup: log to data/logs/pipeline.log and console
    default_log_path = DEFAULT_LOG_DIR / DEFAULT_LOG_FILE
    return setup_logger(
        name, 
        log_file=str(default_log_path), 
        console=True, 
        level=_log_level
    )


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


def set_global_log_level(level: int) -> None:
    """
    Set the global logging level for all new loggers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.WARNING)
    """
    global _log_level
    _log_level = level