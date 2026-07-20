"""
Logger utility module for the llmXive science pipeline.

Provides a centralized logging configuration loader and a
factory function to retrieve configured logger instances.
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

    Looks in the project root relative to the code directory,
    or falls back to the current working directory.
    """
    # Try relative to this file's location (code/src/utils/)
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "logs" / "logging.conf"

    if not config_path.exists():
        # Fallback to common locations
        fallback_paths = [
            Path.cwd() / "logs" / "logging.conf",
            Path.cwd() / "logging.conf",
            project_root / "logging.conf",
        ]
        for fallback in fallback_paths:
            if fallback.exists():
                return fallback

    return config_path


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance configured by logging.conf.

    Args:
        name: Optional name for the logger. If None, returns the root logger.

    Returns:
        A configured logging.Logger instance.

    Raises:
        FileNotFoundError: If logging.conf cannot be found.
        ValueError: If the configuration file is invalid.
    """
    config_path = _get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"Logging configuration file not found at {config_path}. "
            "Please ensure logs/logging.conf exists (Task T006a)."
        )

    # Load configuration from file
    logging.config.fileConfig(
        fname=str(config_path),
        disable_existing_loggers=False,
    )

    return logging.getLogger(name)