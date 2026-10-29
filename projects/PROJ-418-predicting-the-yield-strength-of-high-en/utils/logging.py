"""
utils/logging.py
-----------------

Centralised logging utilities used throughout the project. Provides:

* ``get_logger(name)`` – returns a configured ``logging.Logger`` instance.
* ``set_seeds(seed)`` – seeds the common random-number generators to
  guarantee reproducibility for the pipeline scripts.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Optional

import numpy as np


def get_logger(name: str, *, log_file: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger with a sensible default configuration.

    Parameters
    ----------
    name : str
        Name of the logger (usually ``__name__``).
    log_file : str, optional
        If provided, a ``FileHandler`` writing to ``log_file`` is added.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def set_seeds(seed: int = 42) -> None:
    """
    Seed the random number generators used by the project to ensure
    deterministic behaviour.

    Parameters
    ----------
    seed : int, default 42
        Seed value applied to ``random``, ``numpy.random`` and the
        ``PYTHONHASHSEED`` environment variable.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)