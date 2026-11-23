"""
Logging infrastructure for the resting-state fMRI entropy project.

This module configures a centralized logging system that:
1. Writes detailed logs to a rotating file in `data/logs/`.
2. Provides a consistent logger instance for the entire pipeline.
3. Supports different log levels (DEBUG, INFO, WARNING, ERROR).
"""
import os
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Format for log messages
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure the root logger and create a project-specific logger.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to the log file. Defaults to data/logs/pipeline.log.
        console_output: If True, also logs to stderr.

    Returns:
        A configured logger instance for the project.
    """
    global _logger

    if _logger is not None:
        return _logger

    # Determine log file path
    if log_file is None:
        log_file = LOG_FILE
    else:
        # Ensure custom log file directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create a custom logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File handler (RotatingFileHandler to prevent huge logs)
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10_000_000, backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        # Fallback if write permission is denied
        logger.warning(f"Could not write to log file {log_file}. Logging to console only.")

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module or the project root.

    Args:
        name: The name of the logger (e.g., "download", "preprocess").
             If None, returns the root project logger.

    Returns:
        A configured logger instance.
    """
    if _logger is None:
        # Auto-initialize if not explicitly set up
        setup_logging()

    if name:
        return _logger.getChild(name)
    return _logger


# Initialize logging with default settings immediately upon import
# This ensures logs are available even if the user doesn't explicitly call setup_logging()
setup_logging()

# Convenience function to get the root logger
root_logger = get_logger()