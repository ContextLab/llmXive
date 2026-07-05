"""
Logging infrastructure for the llmXive molecular reactivity pipeline.

Provides a centralized logging configuration that ensures consistent
formatting, file rotation, and log levels across the project.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Constants for log configuration
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure the results directory exists for log files
LOG_DIR = Path("results")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger registry to prevent duplicate handlers
_configured_loggers = set()


def get_logger(name: str, log_file: Optional[str] = None, level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Retrieve or create a logger with the specified name.

    If the logger hasn't been configured yet, it sets up:
    - A console handler with standard formatting
    - An optional file handler if log_file is provided
    - The specified log level

    Args:
        name: The name of the logger (typically __name__ of the module).
        log_file: Optional relative path to a log file within the results/ directory.
        level: The logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid re-configuring if already set up to prevent duplicate handlers
    if name in _configured_loggers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_path = LOG_DIR / log_file
        try:
            # Use RotatingFileHandler to prevent log files from growing indefinitely
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to console-only if file creation fails
            logger.warning(f"Failed to create log file {file_path}: {e}")

    _configured_loggers.add(name)
    return logger


def setup_root_logger(level: int = DEFAULT_LOG_LEVEL) -> None:
    """
    Configure the root logger for the entire application.

    This should be called once at the entry point of the application
    to ensure all child loggers inherit the correct configuration.

    Args:
        level: The logging level for the root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates if this is called multiple times
    root_logger.handlers.clear()

    # Console handler for root
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Default file handler for the main pipeline log
    try:
        main_log_path = LOG_DIR / "pipeline.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Could not initialize root file handler: {e}")


# Convenience alias for the main pipeline logger
def get_pipeline_logger() -> logging.Logger:
    """
    Get the main pipeline logger.

    Returns:
        The configured logger named 'llmXive.pipeline'.
    """
    return get_logger("llmXive.pipeline", log_file="pipeline.log")
