"""
Project‑wide logger utilities.

This module provides a simple, file‑based logger that writes INFO and
WARNING (and higher) messages to ``logs/pipeline.log``.  The logger is
lazily instantiated; the first call creates the log directory and the
file handler.  Subsequent calls return the same ``logging.Logger``
instance without adding duplicate handlers.

The design matches the expectations of other pipeline components that
import ``setup_logging``, ``get_logger`` and ``log_warning`` from
``code.utils.logging_config`` – those functions are thin wrappers around
the implementations defined here.
"""

import logging
from pathlib import Path
from typing import Optional

# Path to the pipeline log file (relative to the project root)
LOG_FILE = Path("logs/pipeline.log")


def _ensure_log_dir() -> None:
    """Create the ``logs`` directory if it does not already exist."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Return a configured logger that writes to ``logs/pipeline.log``.

    The logger is created only once per ``name``; if a logger with the
    given name already has handlers attached, it is returned unchanged.
    This prevents duplicate log entries when the function is called
    multiple times throughout the pipeline.

    Parameters
    ----------
    name: str, optional
        The logger name.  The default ``\"pipeline\"`` is used by most
        pipeline modules.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    _ensure_log_dir()
    logger = logging.getLogger(name)

    # Attach a file handler only once
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_warning(message: str) -> None:
    """
    Convenience wrapper to log a warning message.

    Parameters
    ----------
    message: str
        The warning text to be recorded.
    """
    get_logger().warning(message)


def setup_logging() -> None:
    """
    Initialise the logging system.

    The function exists for backward‑compatibility with modules that
    previously called ``utils.logging_config.setup_logging()``.  It simply
    ensures that the singleton logger is instantiated.
    """
    get_logger()
