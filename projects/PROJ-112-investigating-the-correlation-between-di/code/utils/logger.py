"""
Standardized logging configuration for the llmXive research pipeline.

Provides a centralized logger factory that ensures consistent formatting,
file output, and console output across all project modules.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Project root is assumed to be the parent of 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_FILE = _LOG_DIR / "pipeline.log"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global cache to prevent re-configuring loggers unnecessarily
_LOGGERS: dict = {}

_DEFAULT_FORMATTER = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def _get_file_handler() -> logging.FileHandler:
    """Create a file handler that writes to the project's log file."""
    handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    handler.setFormatter(_DEFAULT_FORMATTER)
    handler.setLevel(logging.DEBUG)
    return handler

def _get_console_handler() -> logging.StreamHandler:
    """Create a console handler for stdout/stderr."""
    handler = logging.StreamHandler()
    handler.setFormatter(_DEFAULT_FORMATTER)
    handler.setLevel(logging.INFO)
    return handler

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a configured logger instance.

    Args:
        name: Optional module name. If None, defaults to 'llmXive'.

    Returns:
        A configured logging.Logger instance.
    """
    if name is None:
        name = "llmXive"

    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times if called repeatedly
    if not logger.handlers:
        logger.addHandler(_get_file_handler())
        logger.addHandler(_get_console_handler())

    # Ensure propagation is controlled (usually False for root-like loggers in apps)
    logger.propagate = False

    _LOGGERS[name] = logger
    return logger
