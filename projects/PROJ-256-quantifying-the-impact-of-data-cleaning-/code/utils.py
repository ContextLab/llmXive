import logging
import os
import random
import hashlib
from typing import Any, Optional
import numpy as np

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
        Hexadecimal SHA256 digest.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()


def pin_random_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across the standard library ``random``,
    NumPy, and the Python hash seed.

    Parameters
    ----------
    seed: int, optional
        The seed value to set. Defaults to 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Flexible logging configuration.

    This function tolerates a variety of call signatures used throughout the
    codebase, for example:

    - ``setup_logging("INFO")``
    - ``setup_logging(name="my_logger", log_level="DEBUG")``
    - ``setup_logging("my_logger", "WARNING")``
    - ``setup_logging()`` (defaults to ``name="main"`` and ``level="INFO"``)

    Parameters
    ----------
    *args : tuple
        Positional arguments – interpreted as ``(name,)`` or ``(log_level,)``
        or ``(name, log_level)`` depending on count and content.
    **kwargs : dict
        Keyword arguments – ``name`` and ``log_level`` can be supplied
        explicitly.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    # Default values
    name = "main"
    level = "INFO"

    # Resolve positional arguments
    if args:
        if len(args) == 1:
            # Could be a name or a log level
            if isinstance(args[0], str) and args[0].upper() in logging._nameToLevel:
                level = args[0].upper()
            else:
                name = args[0]
        elif len(args) >= 2:
            name, level_candidate = args[0], args[1]
            name = name
            if isinstance(level_candidate, str) and level_candidate.upper() in logging._nameToLevel:
                level = level_candidate.upper()

    # Resolve keyword arguments (override positional if present)
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = kwargs["log_level"].upper()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Ensure at least one handler exists to avoid “No handlers could be found” warnings
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
