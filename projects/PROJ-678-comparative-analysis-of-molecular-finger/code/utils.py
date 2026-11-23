"""
Utility module for the comparative analysis pipeline.
Provides functions for logging configuration, random seed initialization,
and logger retrieval used across the codebase.
"""

import logging
import os
import random
import numpy as np

__all__ = [
    "setup_logging",
    "init_random_seed",
    "get_logger",
]

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger with a simple format and return a logger
    instance. This function is imported by many pipeline scripts (e.g.,
    `download.py`, `fingerprints.py`, `split.py`, `train.py`, `evaluate.py`).

    Parameters
    ----------
    level : int, optional
        Logging level for the root logger (default is ``logging.INFO``).

    Returns
    -------
    logging.Logger
        The root logger instance.
    """
    # Basic configuration; if the root logger is already configured this call
    # is a no‑op, which is safe for repeated imports.
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger()

def init_random_seed(seed: int = 42) -> None:
    """
    Initialise the random seed for the Python standard library,
    NumPy, and the environment variable ``PYTHONHASHSEED`` to ensure
    reproducibility across runs.

    Parameters
    ----------
    seed : int, optional
        Seed value (default is ``42``).
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger. All pipeline modules use this helper to obtain
    a logger that respects the configuration performed by ``setup_logging``.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return logging.getLogger(name)
