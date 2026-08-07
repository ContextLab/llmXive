"""
seeds.py - Global seed management for reproducibility.
"""
import random
import os
from typing import Optional, List, Union, Any
import numpy as np

_global_seed: Optional[int] = None

def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set the global random seed for reproducibility.
    If seed is None, uses an environment variable or a default value.
    """
    global _global_seed
    if seed is None:
        seed_str = os.environ.get("LLMXIVE_SEED", "42")
        seed = int(seed_str)
    
    _global_seed = seed
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch is not imported here to avoid dependency on torch if not needed
    # If torch is needed, it should be imported inside the function or by the caller
    return seed

def get_seed() -> Optional[int]:
    """Get the currently set global seed."""
    return _global_seed

def reset_seed() -> None:
    """Reset the global seed to None (uninitialized)."""
    global _global_seed
    _global_seed = None
