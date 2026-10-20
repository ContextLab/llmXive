"""
Simple logging utilities used throughout the project.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

_LOGGER = None


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure the root logger.

    Parameters
    ----------
    log_level : str
        Logging level name (e.g. ``\"INFO\"``).
    log_file : str, optional
        If provided, a file handler writing to this path is added.
    """
    global _LOGGER
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Console handler (always present)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Optional file handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _LOGGER = logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger; initialise the global logger if necessary.
    """
    global _LOGGER
    if _LOGGER is None:
        setup_logging()
    return logging.getLogger(name)