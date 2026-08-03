"""
Utility functions for the llmXive research pipeline.

Provides logging setup, deterministic seeding, and SHA-256 hashing utilities.
"""
import hashlib
import logging
import os
import random
from typing import Optional, Union

import numpy as np

# Try to import torch, but allow the module to load even if torch is not present
# for utility functions that don't require it.
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    logger_name: str = "llmXive"
) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handlers.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, only console output is used.
        logger_name: Name of the logger to configure or retrieve.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def set_deterministic_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across numpy, python, and torch (if available).

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)

    if TORCH_AVAILABLE and torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CUDA operations
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False


def compute_sha256(data: Union[str, bytes]) -> str:
    """
    Compute the SHA-256 hash of the input data.

    Args:
        data: String or bytes to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    return hashlib.sha256(data).hexdigest()
