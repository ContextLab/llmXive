"""
Logging configuration and helper functions.
Provides a centralized way to configure logging for the entire pipeline.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Default log level can be overridden by environment variable
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """
    Configure the root logger with console and optional file handlers.

    Args:
        level: Log level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR').
               Defaults to LOG_LEVEL env var or 'INFO'.
        log_file: Path to log file. If None, logs only to console.
        console: Whether to log to console.
    """
    log_level = getattr(logging, (level or DEFAULT_LOG_LEVEL), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []  # Clear existing handlers

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log startup info
    logging.info("Logging initialized at level %s", log_level)
    if log_file:
        logging.info("Logs will be written to: %s", log_path.resolve())

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    logger_name = name or __name__.split(".")[0]
    return logging.getLogger(logger_name)
