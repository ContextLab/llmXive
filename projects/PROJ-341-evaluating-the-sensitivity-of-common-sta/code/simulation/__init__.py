"""
Simulation module initialization.
Implements T006: Deterministic random seed manager.
"""
import numpy as np
from typing import Optional

_GLOBAL_SEED = None
_GLOBAL_RNG = None

def set_seed(seed: int):
    """Set the global random seed."""
    global _GLOBAL_SEED, _GLOBAL_RNG
    _GLOBAL_SEED = seed
    _GLOBAL_RNG = np.random.default_rng(seed)

def get_seed() -> Optional[int]:
    """Get the global random seed."""
    return _GLOBAL_SEED

def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Get a random number generator.
    If seed is provided, use it. Otherwise, use the global seed.
    """
    global _GLOBAL_RNG
    if seed is not None:
        return np.random.default_rng(seed)
    if _GLOBAL_RNG is None:
        # Default seed if not set
        _GLOBAL_RNG = np.random.default_rng(42)
    return _GLOBAL_RNG

def reset_rng():
    """Reset the random number generator."""
    global _GLOBAL_RNG
    _GLOBAL_RNG = None
    _GLOBAL_SEED = None

def main():
    """Main entry point for testing."""
    pass

if __name__ == "__main__":
    main()