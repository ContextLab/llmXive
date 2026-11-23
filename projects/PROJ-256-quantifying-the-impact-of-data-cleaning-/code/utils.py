"""
Utility functions for the project.
Consolidated functionality from previous modules:
- cleanup_utils.py
- profiler.py

This module now provides:
* pin_random_seed: set seeds for reproducibility across libraries.
* compute_file_checksum: SHA256 checksum of a file.
* setup_logging: flexible logger configuration supporting multiple call signatures.
* Any additional helper functions that were previously defined in the removed modules
  can be added here as needed.
"""
import logging
import random
import os
import hashlib
from pathlib import Path
from typing import Any

def pin_random_seed(seed: int) -> None:
    """
    Pin the random seed for reproducibility across the standard libraries.

    Args:
        seed (int): The seed value to set.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass


def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        filepath (str): Path to the file.

    Returns:
        str: Hexadecimal SHA256 checksum.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Flexible logging configuration.

    Accepts a variety of calling conventions used throughout the codebase:
    - setup_logging()
    - setup_logging("INFO")
    - setup_logging(log_level="DEBUG")
    - setup_logging(name="my_logger")
    - setup_logging("my_logger", "WARNING")
    - setup_logging(log_level="INFO", name="custom")

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Determine logger name and level from positional or keyword arguments
    name: str | None = None
    level: str = "INFO"

    if args:
        if len(args) == 1:
            # Could be either level or name; decide by checking known level strings
            if isinstance(args[0], str) and args[0].upper() in logging._nameToLevel:
                level = args[0]
            else:
                name = args[0]
        elif len(args) >= 2:
            name, level = args[0], args[1]

    # Keyword overrides
    if "log_level" in kwargs:
        level = kwargs["log_level"]
    if "name" in kwargs:
        name = kwargs["name"]

    logger = logging.getLogger(name) if name else logging.getLogger()
    logger.setLevel(logging._nameToLevel.get(level.upper(), logging.INFO))

    # Ensure at least one handler exists to avoid "No handlers could be found" warnings
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
