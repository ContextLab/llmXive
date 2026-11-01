"""
Utility module providing structured logging and deterministic seeding.

The project uses a single logger factory ``get_logger`` that returns a
``logging.Logger`` instance.  The logger is configured with a basic
format and, optionally, a file handler if ``log_file`` is supplied.

``set_seed`` pins the random seeds for the standard libraries used in
the pipeline (``random``, ``numpy``, ``pandas`` and ``sklearn``) to
satisfy the Constitution Principle I.
"""

import logging
import random
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.utils import check_random_state

_loggers = {}

def get_logger(name: str, *, log_file: Optional[str] = None) -> logging.Logger:
    """
    Return a configured ``logging.Logger`` instance.

    Parameters
    ----------
    name: str
        Name of the logger (usually ``__name__``).
    log_file: Optional[str]
        Path to a file where log records should be written.  If omitted,
        logging is performed only to ``stderr``.

    Returns
    -------
    logging.Logger
        Configured logger.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if this function is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, mode="a")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger

def set_seed(seed: int) -> None:
    """
    Seed the random number generators used throughout the project.

    This function is called early in the pipeline (see ``src/main.py``)
    to guarantee reproducibility.

    Parameters
    ----------
    seed: int
        The integer seed to set for all libraries.
    """
    random.seed(seed)
    np.random.seed(seed)
    # pandas uses numpy's RNG internally, so seeding numpy is sufficient.
    # sklearn utilities accept ``random_state`` arguments; we provide a
    # helper that returns a ``np.random.RandomState`` instance.
    # The call below simply validates the seed.
    _ = check_random_state(seed)
