"""
Random seed pinning utility for reproducible experiments.

This module provides functions to set random seeds for Python's built-in
random module and NumPy to ensure deterministic behavior across runs.
"""

import random
from typing import Optional

import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across the pipeline.
    
    This function sets the seed for:
    - Python's built-in random module
    - NumPy's random number generator
    
    Args:
        seed (int): The random seed value to use. Must be a non-negative integer.
        
    Raises:
        ValueError: If seed is not a non-negative integer.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")
    
    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    logger.info(f"Random seed pinned to {seed} for reproducibility")


def get_seed_from_config() -> int:
    """
    Retrieve the random seed from the project configuration.
    
    This function attempts to read the seed from an environment variable
    or falls back to a default value (42) if not set.
    
    Returns:
        int: The seed value to use.
    """
    import os
    
    seed_str = os.getenv("PYTHONHASHSEED") or os.getenv("RANDOM_SEED", "42")
    
    try:
        seed = int(seed_str)
        if seed < 0:
            raise ValueError("Seed must be non-negative")
        return seed
    except ValueError as e:
        logger.warning(f"Invalid seed value '{seed_str}', defaulting to 42. Error: {e}")
        return 42