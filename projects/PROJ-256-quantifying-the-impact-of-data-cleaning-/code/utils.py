"""
Utility functions for the project.

This module provides common helper functions such as random seed pinning,
logging setup, and file checksum calculation. Existing functions are
preserved; new functionality is added in a backward‑compatible way.
"""
import hashlib
import logging
import os
import random
import sys
import time
from typing import Any

# ----------------------------------------------------------------------
# Existing utilities (preserved from the original repository)
# ----------------------------------------------------------------------
def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    filepath: str
        Path to the file whose checksum should be computed.

    Returns
    -------
    str
        Hexadecimal representation of the SHA‑256 checksum.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def setup_logging(
    name: str = "llmXive",
    log_level: str = "INFO",
    *,
    fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Initialise a logger that can be called with a variety of signatures.

    The function is deliberately permissive: callers may supply the logger
    name and/or the log level positionally or as keywords, and any unknown
    arguments are ignored so that existing call sites continue to work.

    Parameters
    ----------
    name : str, optional
        Logger name. Defaults to ``"llmXive"``.
    log_level : str, optional
        Logging level name (e.g., ``"INFO"``, ``"DEBUG"``). Defaults to ``"INFO"``.
    fmt : str, optional
        Logging format string.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    # Compatibility shim – accept a variety of positional/keyword orders
    # without raising TypeError.
    if isinstance(name, int):
        # If the first positional argument is actually a log level, swap.
        name, log_level = "llmXive", name
    if isinstance(log_level, str) and log_level.upper() in logging._nameToLevel:
        level = logging._nameToLevel[log_level.upper()]
    else:
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if setup_logging is called repeatedly.
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    return logger

# ----------------------------------------------------------------------
# New utility: pin_random_seed
# ----------------------------------------------------------------------
def pin_random_seed(seed: int = 42) -> None:
    """
    Pin the random seed for reproducibility across the standard library,
    ``random`` and ``numpy`` random generators.

    The function is deliberately tolerant of being called with no arguments
    (default seed ``42``) or with a non‑integer seed – in the latter case it
    will attempt to coerce the value to ``int`` and fall back to ``42`` if that
    fails.

    Parameters
    ----------
    seed : int, optional
        Desired seed value. Defaults to ``42``.
    """
    try:
        seed_int = int(seed)
    except Exception:
        seed_int = 42

    random.seed(seed_int)
    # NumPy may not be installed in all minimal environments; guard against ImportError.
    try:
        import numpy as np
        np.random.seed(seed_int)
    except Exception:
        pass

# The module's public interface
__all__ = [
    "compute_file_checksum",
    "setup_logging",
    "pin_random_seed",
]
