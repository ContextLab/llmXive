"""
Logger utility module for the llmXive research pipeline.

Provides a centralized `get_logger()` function that loads the logging
configuration from `logging.conf` (located in the project root or code root)
and returns a configured logger instance.
"""
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

from src.config import get_config


def _get_config_path() -> Path:
    """
    Locate the logging.conf file.

    Searches in the following order:
    1. Relative to the current working directory (project root)
    2. Relative to the code root (code/)
    3. Relative to this module's directory (code/src/utils/)

    Raises:
        FileNotFoundError: If logging.conf is not found in any expected location.
    """
    possible_paths = [
        Path.cwd() / "logging.conf",
        Path.cwd() / "code" / "logging.conf",
        Path(__file__).parent.parent / "logging.conf",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"logging.conf not found. Expected locations: {possible_paths}"
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance configured via logging.conf.

    This function ensures the logging configuration is loaded exactly once
    and returns a logger with the specified name (or the root logger if None).

    Args:
        name: Optional name for the logger. If None, returns the root logger.

    Returns:
        A configured logging.Logger instance.

    Raises:
        FileNotFoundError: If logging.conf is missing.
        ValueError: If the logging configuration is invalid.
    """
    config_path = _get_config_path()

    # Load configuration from file
    logging.config.fileConfig(
        config_path,
        disable_existing_loggers=False,
    )

    # Get and return the requested logger
    logger = logging.getLogger(name)
    return logger