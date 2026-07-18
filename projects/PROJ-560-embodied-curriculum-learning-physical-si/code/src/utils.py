"""
Utility functions for the project.
"""
import random
import os
from typing import Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility.

    Args:
        seed (int): The seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    logger.info(f"Random seed set to {seed}")
