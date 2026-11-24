"""
Logging infrastructure for the project.

This module provides two public functions:
  - ``setup_logging()``: Configures the root logger with a console and a file
    handler using the settings defined in :pymod:`code.config`.
  - ``get_logger(name)``: Returns a logger with the given name. The first
    call to ``get_logger`` (or an explicit call to ``setup_logging``)
    ensures that the logging system is initialized exactly once.

The implementation guarantees that the log directory exists, that duplicate
handlers are not added on repeated imports, and that the logger hierarchy
respects the configured log level and format.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Import configuration constants. ``code.config`` is located at the project
# root ``code/config.py`` and is importable as ``config`` because the
# repository root is added to ``PYTHONPATH`` during execution.
from config import LOG_LEVEL, LOG_FORMAT, LOGS_DIR

# Module‑level flag to avoid configuring the root logger multiple times.
_LOGGING_INITIALIZED: bool = False

def _ensure_log_directory() -> Path:
    """
    Ensure that the directory specified by ``LOGS_DIR`` exists.

    Returns
    -------
    Path
        The absolute path to the log directory.
    """
    log_path = Path(LOGS_DIR)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path

def setup_logging() -> None:
    """
    Configure the root logger.

    This function creates a console handler and a file handler (``pipeline.log``
    inside ``LOGS_DIR``) with the level and format defined in the configuration.
    It is safe to call multiple times; the handlers will only be added once.
    """
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED:
        # Logging is already configured – nothing to do.
        return

    # Ensure the log directory exists before creating the file handler.
    log_dir = _ensure_log_directory()

    # Resolve the numeric log level from the string (e.g., "INFO").
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    # Create handlers.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)

    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setLevel(numeric_level)

    # Define formatter and attach it to both handlers.
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Configure the root logger.
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Guard against adding duplicate handlers if other libraries have already
    # attached their own handlers. We only add our handlers if they are not
    # already present.
    existing_handlers = {type(h) for h in root_logger.handlers}
    if logging.StreamHandler not in existing_handlers:
        root_logger.addHandler(console_handler)
    if logging.FileHandler not in existing_handlers:
        root_logger.addHandler(file_handler)

    _LOGGING_INITIALIZED = True

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger, ensuring that the logging system is initialized.

    Parameters
    ----------
    name : str
        The hierarchical name of the logger (e.g., ``"data.download"``).

    Returns
    -------
    logging.Logger
        The requested logger instance.
    """
    # Initialise logging on first use.
    if not _LOGGING_INITIALIZED:
        setup_logging()
    return logging.getLogger(name)