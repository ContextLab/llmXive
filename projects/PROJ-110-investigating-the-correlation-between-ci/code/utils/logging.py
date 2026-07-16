"""
Base logging infrastructure for the llmXive research pipeline.

Provides a configurable logger with both file and console handlers.
Ensures logs are written to `data/logs/` and the console simultaneously.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure the logs directory exists relative to the project root
# Assuming standard project structure: code/utils/ -> ../../data/logs/
_LOGS_DIR = Path(__file__).parent.parent.parent / "data" / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Default log format
_DEFAULT_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance cache to prevent duplicate handlers
_LOGGERS = {}


def get_logger(name: str = "llmXive", level: int = logging.INFO) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.

    If the logger already exists, it returns the existing instance.
    If not, it creates a new one with file and console handlers.

    Args:
        name: The name of the logger (usually __name__ of the caller).
        level: The logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        A configured logging.Logger instance.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if they already exist (in case of re-imports)
    if logger.handlers:
        _LOGGERS[name] = logger
        return logger

    # Create formatter
    formatter = logging.Formatter(_DEFAULT_FORMAT, datefmt=_DATE_FORMAT)

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler
    # Generate a log file name based on timestamp to avoid overwriting previous runs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"pipeline_{timestamp}.log"
    log_path = _LOGS_DIR / log_filename

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Log the initialization of the logger
    logger.info(f"Logger '{name}' initialized. Logging to: {log_path}")

    _LOGGERS[name] = logger
    return logger


def setup_root_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function to setup the root logger for the entire project.
    Returns the main project logger.
    """
    return get_logger("llmXive.root", level)