import logging
import os
import random
import hashlib
from typing import Any
import numpy as np

_logger_cache = {}

def pin_random_seed(seed: int) -> None:
    """Set seeds for reproducibility across numpy and the Python stdlib."""
    random.seed(seed)
    np.random.seed(seed)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Create or retrieve a logger.

    This function is deliberately permissive: callers may provide a log level
    as the first positional argument, as a named keyword ``log_level``, or even
    a custom logger name. Any unexpected arguments are ignored so that the
    function remains compatible with all existing call sites.
    """
    # Resolve logger name / level
    log_level = kwargs.get("log_level")
    if not log_level and args:
        # First positional argument may be a level string or a logger name
        if isinstance(args[0], str):
            # Heuristic: if it looks like a logging level, use it; otherwise treat as name
            possible_level = args[0].upper()
            if possible_level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
                log_level = possible_level
            else:
                logger_name = args[0]
                return _logger_cache.setdefault(logger_name, _configure_logger(logger_name, log_level))
        else:
            logger_name = str(args[0])
            return _logger_cache.setdefault(logger_name, _configure_logger(logger_name, log_level))

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