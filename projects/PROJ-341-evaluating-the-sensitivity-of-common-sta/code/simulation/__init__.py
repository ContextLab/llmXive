"""
Simulation Module Initialization.

Provides a deterministic random seed manager to enforce reproducibility
across all simulation modules (Task T006).
"""
import numpy as np
from typing import Optional, Dict, Any
import json
import os

_rng_instance: Optional[np.random.Generator] = None
_seed_value: Optional[int] = None

def set_seed(seed: int) -> None:
    """
    Sets the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    global _rng_instance, _seed_value
    _seed_value = seed
    _rng_instance = np.random.default_rng(seed)

def get_rng() -> np.random.Generator:
    """
    Returns the global RNG instance.
    
    Raises:
        RuntimeError: If the seed has not been set yet.
    """
    global _rng_instance
    if _rng_instance is None:
        # Default to a fixed seed if not set, for safety in testing
        # In production, this should be explicitly set by the main entry point
        set_seed(42) 
    return _rng_instance

def get_seed() -> Optional[int]:
    """
    Returns the current seed value.
    """
    global _seed_value
    return _seed_value

def reset_seed() -> None:
    """
    Resets the RNG to its initial state if a seed was set.
    """
    global _rng_instance, _seed_value
    if _seed_value is not None:
        _rng_instance = np.random.default_rng(_seed_value)
    else:
        _rng_instance = None

# Initialize with a default seed for immediate usability, 
# but production code should call set_seed explicitly.
set_seed(42)
