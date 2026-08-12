"""
code/utils/seeds.py

Random seed management for reproducible sampling and statistical resampling.
"""
import random
import numpy as np
import os
from typing import Optional

_seed_manager = None

class SeedManager:
    def __init__(self, seed: int):
        self.seed = seed
        self._set_seeds()

    def _set_seeds(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        # For Python's hash randomization if needed (though usually per-process)
        os.environ['PYTHONHASHSEED'] = str(self.seed)

def set_global_seed(seed: int = 42) -> None:
    """
    Set global random seeds for reproducibility.
    """
    global _seed_manager
    _seed_manager = SeedManager(seed)

def get_seed_manager() -> Optional[SeedManager]:
    """
    Get the current seed manager instance.
    """
    return _seed_manager

def sample_with_seed(data: list, k: int, seed: Optional[int] = None) -> list:
    """
    Sample k items from data using a specific seed if provided.
    """
    if seed is not None:
        random.seed(seed)
    return random.sample(data, k)
