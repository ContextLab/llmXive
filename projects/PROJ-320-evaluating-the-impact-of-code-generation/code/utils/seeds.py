"""
Seed management for reproducibility.
"""
import random
import numpy as np
import os
from typing import Optional, List, Any

class SeedManager:
    """Manages global random seeds."""
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.set_global_seed()

    def set_global_seed(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        os.environ['PYTHONHASHSEED'] = str(self.seed)

    def get_seed(self) -> int:
        return self.seed

_SEED_MANAGER: Optional[SeedManager] = None

def set_global_seed(seed: int = 42) -> None:
    global _SEED_MANAGER
    _SEED_MANAGER = SeedManager(seed)

def get_seed_manager() -> Optional[SeedManager]:
    return _SEED_MANAGER

def sample_with_seed(data: List[Any], n: int, seed: Optional[int] = None) -> List[Any]:
    if seed is not None:
        random.seed(seed)
    return random.sample(data, min(n, len(data)))

def get_random_state():
    return random.getstate()

def set_random_state(state):
    random.setstate(state)

def main():
    set_global_seed(123)
    print(f"Random sample: {sample_with_seed([1,2,3,4,5], 3)}")

if __name__ == "__main__":
    main()
