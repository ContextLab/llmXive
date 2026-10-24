"""
Package initialization for the project.

Provides a small helper to configure logging in a reproducible way.
The test suite (`tests/test_logging.py`) expects a function named
``setup_logging`` to be importable from ``code``.
"""
import logging
import os
from pathlib import Path
from typing import Optional

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Configure a root logger for the package.

    - Clears any existing handlers to avoid duplicate logs.
    - Adds a console ``StreamHandler``.
    - Optionally adds a ``FileHandler``; parent directories are created
      automatically.

    Parameters
    ----------
    level: int
        Logging level (e.g., ``logging.INFO``).
    log_file: str | None
        Path to a log file. If ``None`` only console logging is used.
    format_str: str
        Logging format string.

    Returns
    -------
    logging.Logger
        The configured logger (``logging.getLogger(__name__)``).
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove any existing handlers to start fresh
    for h in list(logger.handlers):
        logger.removeHandler(h)

    formatter = logging.Formatter(format_str)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
