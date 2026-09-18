"""
Logging and seed management utilities.

Provides structured logging configuration and functions to set random seeds
for reproducibility (numpy, pandas, sklearn).
"""
import logging
import numpy as np
import pandas as pd
from typing import Optional
import os
import sys
import random

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger instance with the specified name and level.

    Args:
        name: The name of the logger (usually __name__).
        level: The logging level (default: INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across numpy, pandas, sklearn, and python.

    Args:
        seed: The integer seed value (default: 42).
    """
    random.seed(seed)
    np.random.seed(seed)
    # Pandas doesn't have a global seed, but numpy seed affects its random operations
    os.environ["PYTHONHASHSEED"] = str(seed)
    logger = get_logger(__name__)
    logger.info(f"Random seed set to {seed}")