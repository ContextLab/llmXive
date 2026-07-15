import os
import numpy as np
from typing import Optional
import json

_global_seed = None
_rng_instance = None

def set_seed(seed: int):
    """Set the global random seed for reproducibility."""
    global _global_seed, _rng_instance
    _global_seed = seed
    _rng_instance = np.random.default_rng(seed)

def get_rng(seed: Optional[int] = None):
    """
    Get a random number generator instance.
    
    Args:
        seed: Optional seed. If None, uses global seed or creates a new one.
        
    Returns:
        numpy.random.Generator instance
    """
    global _global_seed, _rng_instance
    
    if seed is not None:
        return np.random.default_rng(seed)
    elif _global_seed is not None:
        return np.random.default_rng(_global_seed)
    else:
        # If no seed is set, use a random one but log it
        s = np.random.integers(0, 2**32)
        return np.random.default_rng(s)

def reset_rng():
    """Reset the RNG to initial state."""
    global _global_seed, _rng_instance
    _global_seed = None
    _rng_instance = None
