import logging
import os
import random
from typing import Any, Optional

import numpy as np
import scipy

# Existing utility functions (pin_random_seed, compute_file_checksum, setup_logging)
# are extended to be tolerant of various call signatures used across the codebase.


def pin_random_seed(seed: int = 0) -> None:
    """
    Set the random seed for reproducibility across ``random``, ``numpy`` and ``scipy``.

    Parameters
    ----------
    seed : int, optional
        The seed value to set. Defaults to ``0``.
    """
    random.seed(seed)
    np.random.seed(seed)
    # scipy uses numpy's RNG internally; no separate seeding required.


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
    import hashlib

    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Initialise a ``logging.Logger`` instance.

    This helper is deliberately permissive – many scripts in the repository invoke
    it with a variety of positional and keyword arguments.  The implementation
    therefore normalises the inputs to support the following patterns:

    - ``setup_logging()`` – defaults to ``INFO`` level and a logger named ``"root"``.
    - ``setup_logging("INFO")`` – level supplied positionally.
    - ``setup_logging("my_logger", "WARNING")`` – name then level.
    - ``setup_logging(log_level="DEBUG")`` – keyword‑only level.
    - ``setup_logging(name="my_logger")`` – keyword‑only name.
    - ``setup_logging("my_logger", log_level="ERROR")`` – mixed positional/keyword.

    Any unrecognised combination is ignored and the defaults are used.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    # Determine logger name and level from the flexible signature.
    name: str = "root"
    level: str = "INFO"

    # Positional arguments handling.
    if args:
        # First positional arg could be a name or a level.
        if isinstance(args[0], str):
            if args[0].upper() in logging._nameToLevel:
                level = args[0].upper()
            else:
                name = args[0]
            if len(args) > 1 and isinstance(args[1], str):
                level = args[1].upper()

    # Keyword arguments handling – they override positional parsing.
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = str(kwargs["log_level"]).upper()
    elif "level" in kwargs:
        level = str(kwargs["level"]).upper()

    logger = logging.getLogger(name)
    logger.setLevel(logging._nameToLevel.get(level, logging.INFO))

    # Ensure at least one handler (avoid duplicate handlers on repeated calls).
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger