import logging
import os
import hashlib
import numpy as np
from typing import Any

# ----------------------------------------------------------------------
# Utility functions for the project
# ----------------------------------------------------------------------

def pin_random_seed(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility across numpy and the standard
    library ``random`` module.

    Parameters
    ----------
    seed : int, optional
        Seed value to use. Default is 42.
    """
    import random

    random.seed(seed)
    np.random.seed(seed)
    # If other libraries (e.g., torch) are added later they can be seeded here.


def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA256 checksum of a file.

    Parameters
    ----------
    filepath : str
        Path to the file.

    Returns
    -------
    str
        Hexadecimal SHA256 checksum.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def setup_logging(log_level: str = "INFO", *args: Any, **kwargs: Any) -> logging.Logger:
    """
    Initialise logging for the project.

    This function is deliberately tolerant: it accepts a positional
    ``log_level`` argument, a keyword ``log_level`` argument, or no argument
    at all.  Additional ``*args``/``**kwargs`` are ignored so that callers
    with different signatures do not raise errors.

    Parameters
    ----------
    log_level : str, optional
        Logging level name (e.g., "INFO", "DEBUG"). If omitted, defaults
        to "INFO".

    Returns
    -------
    logging.Logger
        Configured root logger.
    """
    # Resolve the log level (positional takes precedence, then keyword)
    if args:
        level = str(args[0])
    else:
        level = str(kwargs.get("log_level", log_level))

    level = level.upper()
    numeric_level = getattr(logging, level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    return logger
