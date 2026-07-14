import numpy as np
import json
import os
from typing import Optional, Generator

# Global state for random number generation
_rng: Optional[np.random.Generator] = None
_seed: Optional[int] = None

def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Returns a deterministic random number generator.
    If seed is provided, it initializes a new generator with that seed.
    Otherwise, returns the global generator if initialized, or raises an error.
    """
    global _rng, _seed
    
    if seed is not None:
        # If a specific seed is requested, create a temporary generator
        # This ensures reproducibility for specific tasks without affecting global state
        return np.random.default_rng(seed)
    
    if _rng is None:
        raise RuntimeError("Global RNG not initialized. Call set_seed first or pass a seed to get_rng.")
    
    return _rng

def set_seed(seed: int) -> None:
    """
    Initializes the global random number generator with the given seed.
    """
    global _rng, _seed
    _seed = seed
    _rng = np.random.default_rng(seed)

def get_seed() -> Optional[int]:
    """Returns the currently set global seed."""
    return _seed

def reset_seed() -> None:
    """Resets the global RNG state."""
    global _rng, _seed
    _rng = None
    _seed = None

# Initialize with a default seed if needed, but typically set_seed is called by main
# set_seed(42)