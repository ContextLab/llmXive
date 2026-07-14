import logging
import os
import random
import hashlib
from typing import Any, Optional
import numpy as np

_logger_cache = {}

def pin_random_seed(seed: int) -> None:
    """
    Set the seed for reproducibility across numpy, random and any other
    libraries that respect the global seed.
    """
    random.seed(seed)
    np.random.seed(seed)

def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA256 checksum of a file.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Flexible logging initialiser.

    Accepted call signatures (all are supported):
    - setup_logging()
    - setup_logging(log_level="INFO")
    - setup_logging("INFO")
    - setup_logging(name="my_logger", log_level="WARNING")
    - setup_logging("my_logger", "DEBUG")
    - Any combination of positional and keyword arguments where the first
      string argument is interpreted as the logger name (if it does not match a
      known log level) and the next string as the log level.

    The function never raises for unexpected argument patterns; it falls back
    to a default logger named ``"root"`` with level ``WARNING``.
    """
    # Resolve positional arguments
    name: Optional[str] = None
    level: Optional[str] = None

    if args:
        # If first positional looks like a log level, treat it as level
        first = args[0]
        if isinstance(first, str) and first.upper() in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
            level = first.upper()
            if len(args) > 1 and isinstance(args[1], str):
                name = args[1]
        else:
            name = str(first)
            if len(args) > 1 and isinstance(args[1], str):
                level = args[1].upper()

    # Resolve keyword arguments (they override positional if provided)
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = kwargs["log_level"].upper()

    # Default values
    logger_name = name if name else "root"
    log_level = getattr(logging, level, logging.WARNING) if level else logging.WARNING

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Ensure at least one handler exists to avoid "No handlers could be found" warnings
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger_name = kwargs.get("logger_name", "default")
    logger = _logger_cache.get(logger_name)
    if logger is None:
        logger = _configure_logger(logger_name, log_level)
        _logger_cache[logger_name] = logger
    return logger

def _configure_logger(name: str, level: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if level:
        logger.setLevel(level.upper())
    else:
        logger.setLevel(logging.INFO)
    return logger