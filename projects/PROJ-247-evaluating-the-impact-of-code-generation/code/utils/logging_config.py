"""
Logging configuration utilities for the project.

Provides:
- ``setup_project_logging(name: str, log_file: str)`` – returns a configured
  ``logging.Logger`` that writes to both a file (under the project's logs
  directory) and stdout.
- ``get_logger(name: str)`` – thin wrapper around ``logging.getLogger`` that
  ensures the logger has at least one handler attached.
"""

import logging
import sys
from pathlib import Path

from llmxive_toolkit import paths

def _ensure_log_dir(log_path: Path) -> None:
    """Create the parent directory for the log file if it does not exist."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

def setup_project_logging(name: str, log_file: str) -> logging.Logger:
    """
    Create and configure a logger for a given component.

    Parameters
    ----------
    name: str
        Name of the logger (usually the module name).
    log_file: str
        Relative path (within the project) where the log file should be written.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called multiple times.
    if logger.handlers:
        return logger

    # File handler
    log_path = paths.path(log_file)
    _ensure_log_dir(log_path)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Stream (stdout) handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter("%(levelname)s - %(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger, ensuring that at least a default StreamHandler is present.
    This mirrors the behaviour of ``llmxive_toolkit.get_logger`` but guarantees
    that a handler exists even if the toolkit has not been initialised yet.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Attach a simple stdout handler as a fallback.
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(
            logging.Formatter("%(levelname)s - %(message)s")
        )
        logger.addHandler(stream_handler)
        logger.setLevel(logging.INFO)
    return logger
