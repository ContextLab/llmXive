"""
Logging and utility functions.
"""
import logging
import numpy as np
import pandas as pd
from typing import Optional

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent formatting.

    Args:
        name: Logger name.

    Returns:
        Configured Logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility.

    Args:
        seed: Random seed.
    """
    np.random.seed(seed)
    pd.options.mode.chained_assignment = None  # Suppress SettingWithCopyWarning
    logger = get_logger(__name__)
    logger.info(f"Random seed set to {seed}")