import random
import os
from typing import Optional, Dict, Any, Generator
from pathlib import Path
import numpy as np
from utils.logging import get_logger, info, debug

_global_seed: Optional[int] = None
_is_deterministic: bool = False

def set_global_seed(seed: int):
    global _global_seed, _is_deterministic
    _global_seed = seed
    _is_deterministic = True
    random.seed(seed)
    np.random.seed(seed)
    info(f"Global seed set to {seed}")

def get_global_seed() -> int:
    if _global_seed is None:
        raise RuntimeError("Global seed not set. Call set_global_seed() first.")
    return _global_seed

def is_deterministic() -> bool:
    return _is_deterministic

def generate_seed(base: int = 0) -> int:
    """Generate a new seed based on a base."""
    return base + random.randint(1, 1000000)

def get_rng(seed: int) -> np.random.Generator:
    """
    Factory function to create a new numpy random Generator with a specific seed.
    Returns a new generator for each call, ensuring reproducibility when seeds match.
    """
    return np.random.default_rng(seed)

def ensure_seed_set():
    if _global_seed is None:
        # Default to a random seed if not set, but warn
        warn_seed = random.randint(0, 2**32 - 1)
        set_global_seed(warn_seed)
        get_logger().warning(f"Global seed not set. Using random seed: {warn_seed}")

class SeedContext:
    def __init__(self, seed: int):
        self.seed = seed
        self.original_seed = _global_seed

    def __enter__(self):
        set_global_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_seed is not None:
            set_global_seed(self.original_seed)
        else:
            global _global_seed, _is_deterministic
            _global_seed = None
            _is_deterministic = False
