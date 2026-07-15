import numpy as np
from typing import Optional

_global_seed = None
_rng = None

def set_seed(seed: int) -> None:
    """Set the global random seed."""
    global _global_seed, _rng
    _global_seed = seed
    _rng = np.random.default_rng(seed)

def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """Get a random number generator.
    
    If seed is provided, use it. Otherwise, use the global seed.
    If no global seed is set, use a default seed.
    """
    if seed is not None:
        return np.random.default_rng(seed)
    elif _global_seed is not None:
        return np.random.default_rng(_global_seed)
    else:
        return np.random.default_rng(42)

def get_seed() -> Optional[int]:
    """Get the current global seed."""
    return _global_seed