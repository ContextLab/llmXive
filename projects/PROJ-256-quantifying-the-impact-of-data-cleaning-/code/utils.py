"""
Utility functions for the project.

This module provides:
- `setup_logging`: flexible logger initializer that accepts various argument
  signatures.
- `pin_random_seed`: deterministic seeding of Python's `random`, NumPy's RNG,
  and the built‑in `hash` seed.
- `compute_file_checksum`: compute SHA256 checksum of a file.
- `pin_random_seed` and `setup_logging` are imported by many scripts; they
  must be tolerant to different call patterns.
"""

import logging
import random
import os
import hashlib
from typing import Any, Optional

__all__ = [
    "setup_logging",
    "pin_random_seed",
    "compute_file_checksum",
]


def pin_random_seed(seed: int = 42) -> None:
    """
    Seed the random number generators used throughout the project.

    Parameters
    ----------
    seed : int, optional
        The seed value to use. Defaults to 42.
    """
    random.seed(seed)
    # NumPy's RNG
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        # NumPy may not be installed at import time; ignore if unavailable.
        pass
    # Ensure hash randomisation is disabled for reproducibility
    os.environ["PYTHONHASHSEED"] = str(seed)


def _configure_logger(name: str, level: str) -> logging.Logger:
    """
    Internal helper to configure a logger with the given name and level.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging._nameToLevel.get(level.upper(), logging.INFO))
    if not logger.handlers:
        # Add a simple console handler if none exist.
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def setup_logging(*args: Any, **kwargs: Any) -> logging.Logger:
    """
    Initialise and return a logger.

    This function is deliberately permissive: it accepts the various
    calling conventions observed across the codebase, such as:

    - ``setup_logging()``                     → INFO level, default name.
    - ``setup_logging("INFO")``               → INFO level, default name.
    - ``setup_logging(log_level="DEBUG")``    → DEBUG level, default name.
    - ``setup_logging(name="my_logger")``     → INFO level, custom name.
    - ``setup_logging("my_logger", "WARNING")`` → WARNING level, custom name.
    - Mixed positional/keyword forms.

    Parameters
    ----------
    *args : Any
        Positional arguments – interpreted as ``name`` and/or ``log_level``.
    **kwargs : Any
        Keyword arguments – ``name`` and ``log_level`` are recognised.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    name: Optional[str] = None
    level: str = "INFO"

    # Positional handling
    if len(args) == 1:
        # Could be name or level – guess by looking for known level strings
        if isinstance(args[0], str) and args[0].upper() in logging._nameToLevel:
            level = args[0]
        else:
            name = str(args[0])
    elif len(args) >= 2:
        name = str(args[0])
        level = str(args[1])

    # Keyword handling (overwrites positional if provided)
    if "name" in kwargs:
        name = str(kwargs["name"])
    if "log_level" in kwargs:
        level = str(kwargs["log_level"])

    # Default logger name when none supplied
    if not name:
        name = "project_logger"

    return _configure_logger(name, level)


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
        Hexadecimal SHA256 digest.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
