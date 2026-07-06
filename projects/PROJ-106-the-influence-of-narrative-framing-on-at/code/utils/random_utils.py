import os
import random
import hashlib
from pathlib import Path
from typing import Optional, Union
import numpy as np

_GLOBAL_SEED = None

def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> Optional[int]:
    """Get the current global seed."""
    return _GLOBAL_SEED

def reset_seed() -> None:
    """Reset the global seed to None."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = None

def ensure_seed_set() -> None:
    """
    Ensure a seed is set. If not already set, generate one from system entropy.
    
    This ensures reproducibility while allowing for non-deterministic runs
    when no seed is explicitly provided.
    """
    global _GLOBAL_SEED
    if _GLOBAL_SEED is None:
        # Generate a seed from system entropy
        seed = int(hashlib.sha256(os.urandom(32)).hexdigest(), 16) % (2**32)
        set_global_seed(seed)
        print(f"Generated random seed: {_GLOBAL_SEED}")
