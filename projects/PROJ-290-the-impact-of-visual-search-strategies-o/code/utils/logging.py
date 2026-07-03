"""
Logging infrastructure for the llmXive research pipeline.

Provides a configurable logging setup that writes to both console and file,
with automatic log rotation and structured formatting.
"""
import logging
import os
from pathlib import Path
from typing import Optional

from config import get_config


def setup_logging(
    level: Optional[int] = None,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
               Defaults to Config.LOG_LEVEL if not provided.
        log_dir: Directory for log files. Defaults to Config.LOG_DIR.
        log_file: Log filename. Defaults to Config.LOG_FILE.
        console: Whether to add a console handler. Defaults to True.

    Returns:
        The root logger instance.
    """
    config = get_config()

    # Determine effective settings
    effective_level = level or getattr(logging, config.log_level, logging.INFO)
    effective_log_dir = log_dir or Path(config.log_dir)
    effective_log_file = log_file or config.log_file

    # Ensure log directory exists
    effective_log_dir.mkdir(parents=True, exist_ok=True)

    log_path = effective_log_dir / effective_log_file

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_level)

    # Clear existing handlers to avoid duplicates on repeated calls
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(effective_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(effective_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log startup message
    root_logger.info(
        f"Logging initialized: level={effective_level}, file={log_path}"
    )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
