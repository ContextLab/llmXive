"""
Deterministic logging and random seed management for the HEA Yield Strength Prediction pipeline.

This module provides:
- A deterministic logger configured with a specific seed-based log ID.
- A function to set global random seeds (Python random, NumPy, PyTorch if available)
  to ensure reproducibility across runs.
- Environment variable support for overriding the seed and log ID.
"""
import logging
import os
import random
import sys
from datetime import datetime
from typing import Optional, Union

# Attempt to import optional dependencies for seed setting
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None


# Default configuration
DEFAULT_SEED = 42
DEFAULT_LOG_LEVEL = logging.INFO
LOG_DIR = "output/logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _ensure_log_dir() -> str:
    """Ensure the log directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR


def get_logger(
    name: str,
    seed: Optional[int] = None,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Retrieve or create a logger with deterministic configuration.

    Args:
        name: Name of the logger (usually __name__).
        seed: The random seed to use for this run. If None, uses the env var
              'HEA_SEED' or DEFAULT_SEED.
        log_level: Logging level (e.g., logging.INFO).
        log_to_file: Whether to also log to a file.

    Returns:
        A configured logging.Logger instance.
    """
    if seed is None:
        seed = int(os.getenv("HEA_SEED", DEFAULT_SEED))

    # Ensure reproducibility immediately upon logger creation
    set_seeds(seed)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Stream Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File Handler (deterministic naming based on seed and timestamp)
    if log_to_file:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"run_seed_{seed}_{timestamp}.log"
        log_path = os.path.join(LOG_DIR, log_filename)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging initialized. Log file: {log_path}")

    logger.info(f"Logger '{name}' initialized with seed {seed}")
    return logger


def set_seeds(seed: int) -> None:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.

    Args:
        seed: Integer seed value.
    """
    # Python standard library random
    random.seed(seed)

    # NumPy
    if HAS_NUMPY and np is not None:
        np.random.seed(seed)

    # PyTorch
    if HAS_TORCH and torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior in CUDA operations
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Set environment variable for hash seed to ensure reproducibility in dicts
    os.environ["PYTHONHASHSEED"] = str(seed)


def get_seed() -> int:
    """
    Retrieve the current effective seed from environment or default.

    Returns:
        The integer seed value.
    """
    return int(os.getenv("HEA_SEED", DEFAULT_SEED))