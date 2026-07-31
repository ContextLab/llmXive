"""
Logging utilities for the project.
Provides centralized logging setup and logger retrieval.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_config

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> None:
    """
    Configure the root logger for the project.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional filename for file logging. If None, only logs to console.
        project_root: Optional project root path. If None, uses the default config.
    """
    config = get_config() if project_root is None else None
    if project_root is not None:
        # If a specific project root is passed, we might need a custom config
        # For now, we assume the global config is sufficient or we just use the passed root
        logs_dir = project_root / "logs"
    else:
        logs_dir = config.logs_root

    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = logs_dir / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        A configured logging.Logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)
