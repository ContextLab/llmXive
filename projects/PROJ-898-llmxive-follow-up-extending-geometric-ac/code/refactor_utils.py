"""
Refactored utility functions for llmXive.
Consolidates logging, seeding, and hashing utilities.
"""
import hashlib
import logging
import os
import random
from typing import Optional, Union

import numpy as np

def setup_logging(
    log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """
    Configure logging for the project.

    Args:
        log_file: Optional path to a log file. If None, logs to console only.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def set_deterministic_seed(seed: int) -> None:
    """
    Set seeds for deterministic behavior across numpy, torch (if available),
    python random, and os.environ (PYTHONHASHSEED).

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Attempt to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    # Set environment variable for hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)

def compute_sha256(file_path: Union[str, os.PathLike]) -> str:
    """
    Compute the SHA-256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
