"""
Logging configuration for the Solder Hardness Prediction Pipeline.

This module sets up centralized logging with configurable levels, formats,
and handlers for the entire application.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from config import get_log_level, get_log_format

# Ensure log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / "pipeline.log"


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Configure the root logger for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to value from config.
        log_format: Log message format string. Defaults to value from config.
        log_file: Path to log file. Defaults to data/logs/pipeline.log.
        console_output: Whether to also log to console.
    """
    if log_level is None:
        log_level = get_log_level()
    if log_format is None:
        log_format = get_log_format()
    if log_file is None:
        log_file = str(LOG_FILE)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}", file=sys.stderr)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module or component.

    Args:
        name: Logger name (usually __name__). If None, returns root logger.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


# Initialize logging on module import if not already configured
if not logging.getLogger().handlers:
    setup_logging()
