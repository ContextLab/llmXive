"""
Logging infrastructure for the llmXive research pipeline.

Provides centralized configuration for logging to both console and files,
ensuring consistent formatting and log levels across the project.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from config import load_paths


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure and return a project logger with console and optional file handlers.

    This function sets up a root logger (or a named 'research' logger) with:
    - A console handler outputting to stdout with a specific format.
    - An optional file handler if `log_file` is provided.

    Args:
        log_level: String representation of the log level (e.g., 'DEBUG', 'INFO').
        log_file: Relative path to the log file from the project root. If None,
                  only console logging is configured.
        project_root: The root directory of the project. If None, inferred from
                      the config module.

    Returns:
        logging.Logger: The configured logger instance.

    Examples:
        >>> logger = setup_logging(log_level="DEBUG", log_file="logs/app.log")
        >>> logger.info("Logging initialized successfully")
    """
    # Resolve project root if not provided
    if project_root is None:
        paths = load_paths()
        project_root = paths.get("project_root", Path("."))

    # Ensure log directory exists
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure the logger
    logger = logging.getLogger("research")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (optional)
    if log_file:
        full_log_path = project_root / log_file
        # Ensure parent directories for the log file exist
        full_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(full_log_path))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "research") -> logging.Logger:
    """
    Retrieve a logger by name. Assumes setup_logging has been called.

    Args:
        name: The name of the logger to retrieve.

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)
