import logging
import os
import hashlib
import random
from typing import Any
import numpy as np

def pin_random_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and the
    built‑in ``random`` module.
    """
    random.seed(seed)
    np.random.seed(seed)

def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA256 checksum of a file.

    Parameters
    ----------
    filepath: str
        Path to the file.

    Returns
    -------
    str
        Hex‑encoded SHA256 checksum.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Initialise a logger.  The function is deliberately permissive to satisfy
    the many different call‑sites throughout the project.  It accepts:

    * No arguments – defaults to INFO level.
    * A single positional argument – interpreted as the log level.
    * Keyword argument ``log_level`` – explicit log level.
    * Any additional ``*args``/``**kwargs`` – ignored.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    # Resolve log level
    if args and isinstance(args[0], str):
        log_level = args[0]
    else:
        log_level = kwargs.get("log_level", "INFO")

    # Normalise to a valid level name
    log_level = log_level.upper()
    if log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
        log_level = "INFO"

    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Configure a simple console handler if not already present
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, log_level, logging.INFO))
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
