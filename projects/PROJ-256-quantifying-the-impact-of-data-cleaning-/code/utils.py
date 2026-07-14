"""
utils.py
----------
Utility helpers shared across the project.
"""

import logging
import os
import random
import hashlib
from typing import Optional, Any

import numpy as np

# ----------------------------------------------------------------------
# Logging helper – tolerant to the many calling conventions used in the
# repository.
# ----------------------------------------------------------------------
def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Initialise a logger.

    Accepted signatures (all are compatible with existing call sites):
        setup_logging()
        setup_logging("INFO")
        setup_logging(log_level="INFO")
        setup_logging(name="my_logger", log_level="WARNING")
        setup_logging("my_logger", "DEBUG")
    """
    # Determine logger name and level
    name = None
    level = None

    # Positional handling
    if len(args) == 1:
        # Could be either a level string or a name
        if isinstance(args[0], str):
            # Heuristic: if the string looks like a logging level, treat as level
            if args[0].upper() in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
                level = args[0].upper()
            else:
                name = args[0]
    elif len(args) >= 2:
        name, lvl = args[0], args[1]
        if isinstance(lvl, str):
            level = lvl.upper()

    # Keyword handling overrides positional
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = kwargs["log_level"].upper()

    # Defaults
    if name is None:
        name = __name__
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# ----------------------------------------------------------------------
# Random seed helper – already implemented elsewhere (pin_random_seed)
# ----------------------------------------------------------------------
# Existing functions (pin_random_seed, compute_file_checksum, etc.) are
# defined in other modules and are left untouched.
