"""
Seed management for reproducibility.
"""
import random
import numpy as np
import os
from typing import Optional, List, Any

# Default deterministic seed
SEED = 42

class SeedManager:
    """Manages global random seeds."""
    def __init__(self, seed: int = SEED):
        self.seed = seed
        self.set_global_seed()

    def set_global_seed(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        os.environ['PYTHONHASHSEED'] = str(self.seed)

    def get_seed(self) -> int:
        return self.seed

_SEED_MANAGER: Optional[SeedManager] = None

def set_global_seed(seed: int = SEED) -> None:
    """
    Initialise the global SeedManager with the provided seed.
    This function is retained for backward compatibility.
    """
    global _SEED_MANAGER
    _SEED_MANAGER = SeedManager(seed)

def get_seed_manager() -> Optional[SeedManager]:
    """Return the current SeedManager instance, if any."""
    return _SEED_MANAGER

def sample_with_seed(data: List[Any], n: int, seed: Optional[int] = None) -> List[Any]:
    """
    Sample ``n`` elements from ``data`` using a deterministic seed if provided.
    """
    if seed is not None:
        random.seed(seed)
    return random.sample(data, min(n, len(data)))

def get_random_state():
    """Expose the current state of the Python ``random`` module."""
    return random.getstate()

def set_random_state(state):
    """Restore a previously saved ``random`` state."""
    random.setstate(state)

# ----------------------------------------------------------------------
# Public helper expected by the verification step
# ----------------------------------------------------------------------

def set_seed(seed: int = SEED) -> None:
    """
    Public helper to set deterministic RNG seeds for ``random`` and ``numpy``.
    
    This function mirrors the original specification for task T004.
    It can be imported as:
    
        from code.utils.seeds import set_seed
    
    and will initialise both ``random`` and ``numpy`` RNGs to the given ``seed``.
    """
    # Re‑use the existing SeedManager logic for consistency
    set_global_seed(seed)

def main():
    """Simple demonstration when run as a script."""
    set_seed(123)
    print(f"Random sample: {sample_with_seed([1,2,3,4,5], 3)}")

if __name__ == "__main__":
    main()