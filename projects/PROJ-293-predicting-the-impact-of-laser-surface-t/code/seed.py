"""
Global seed management for reproducible experiments.

This module provides functions to set and retrieve global random seeds
for numpy and the standard random module to ensure reproducibility
across runs.
"""
import random
import numpy as np
from typing import Optional

_GLOBAL_SEED: Optional[int] = None

def set_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value to initialize random number generators.
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> Optional[int]:
    """
    Retrieve the currently set global seed.
    
    Returns:
        The global seed integer if set, None otherwise.
    """
    return _GLOBAL_SEED

def reset_seed() -> None:
    """
    Reset the global seed to None and reinitialize random states.
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = None
    # Note: We do not reset the actual RNG states here as they may
    # be in use by other parts of the system. The next call to set_seed
    # will re-initialize them.

def ensure_seed_set(seed: int = 42) -> None:
    """
    Ensure a seed is set, using the provided value or default if none exists.
    
    Args:
        seed: Default seed value to use if no global seed is currently set.
    """
    if _GLOBAL_SEED is None:
        set_seed(seed)