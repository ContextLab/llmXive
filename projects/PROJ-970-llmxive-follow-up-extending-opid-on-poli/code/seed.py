"""
Seed management module for reproducible experiments.

Implements FR-007 (Reproducibility) and Const I (Seed Initialization).
Provides centralized seed setting for numpy, random, and environment variables.
"""
import os
import random
from typing import Optional

import numpy as np

# Global seed state
_current_seed: Optional[int] = None


def set_seed(seed: int) -> None:
    """
    Initialize all random number generators for reproducibility.
    
    This function must be called at the very start of main.py or runner.py
    before any other operations that use randomness.
    
    Args:
        seed: Integer seed value for reproducibility.
    
    Side effects:
        - Sets numpy.random seed
        - Sets Python random module seed
        - Sets PYTHONHASHSEED environment variable for hash reproducibility
        - Updates global _current_seed state
    
    Raises:
        TypeError: If seed is not an integer.
        ValueError: If seed is negative.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed).__name__}")
    
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    
    global _current_seed
    _current_seed = seed
    
    # Initialize numpy random
    np.random.seed(seed)
    
    # Initialize Python random module
    random.seed(seed)
    
    # Set environment variable for hash reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Log the seed initialization (optional, for debugging)
    # Note: In production, use proper logging infrastructure
    # logging.debug(f"Initialized random seed: {seed}")


def get_seed() -> Optional[int]:
    """
    Get the currently active seed value.
    
    Returns:
        The current seed integer if set_seed() has been called, None otherwise.
    """
    return _current_seed


def initialize_reproducibility(seed: Optional[int] = None) -> int:
    """
    Initialize reproducibility with optional seed parameter.
    
    If no seed is provided, uses the value from config or defaults to 42.
    This is the recommended entry point for main.py and runner.py.
    
    Args:
        seed: Optional explicit seed value. If None, attempts to read from
              config or uses default.
    
    Returns:
        The seed value that was actually used.
    """
    if seed is None:
        # Try to get seed from config if available
        try:
            from config import get_seed as config_get_seed
            seed = config_get_seed()
        except (ImportError, AttributeError):
            # Default seed if config not available
            seed = 42
    
    set_seed(seed)
    return seed