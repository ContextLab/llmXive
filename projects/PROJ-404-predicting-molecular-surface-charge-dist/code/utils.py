import random
import logging
from typing import Optional

import numpy as np
import torch


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across random, numpy, and torch.

    Args:
        seed (int): The integer seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger with a specific name and formatting.

    The log format is: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    Args:
        name (str): The name of the logger (typically __name__).
        level (int): The logging level (default: logging.INFO).

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger