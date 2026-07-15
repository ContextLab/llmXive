import numpy as np
import json
import os

_rng = None
_base_seed = 42

def get_rng(seed: int = None):
    """Get a numpy random generator with deterministic seeding."""
    global _rng
    if seed is not None:
        return np.random.default_rng(seed)
    if _rng is None:
        _rng = np.random.default_rng(_base_seed)
    return _rng

def set_base_seed(seed: int):
    """Set the base seed for the simulation."""
    global _base_seed, _rng
    _base_seed = seed
    _rng = np.random.default_rng(_base_seed)

if __name__ == '__main__':
    print("Simulation Module")
