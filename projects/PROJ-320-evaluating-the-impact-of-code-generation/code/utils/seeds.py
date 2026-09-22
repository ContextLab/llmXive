"""
seeds.py

Manages random seeds for reproducibility in sampling and statistical resampling.
"""
import random
import numpy as np
import os
from typing import Optional, List, Any

class SeedManager:
    """Singleton-like manager for global random seeds."""
    
    _instance = None
    _seed: int = 42
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_seed(self, seed: int):
        """Set the global seed for random and numpy."""
        self._seed = seed
        random.seed(seed)
        np.random.seed(seed)
        # Optionally set os.environ for other libraries if needed
        os.environ['PYTHONHASHSEED'] = str(seed)
    
    def get_seed(self) -> int:
        return self._seed
    
    def get_random_state(self) -> random.Random:
        """Get a new Random instance seeded with the global seed."""
        rng = random.Random(self._seed)
        return rng
    
    def get_numpy_random_state(self) -> np.random.RandomState:
        """Get a new numpy RandomState seeded with the global seed."""
        return np.random.RandomState(self._seed)

def set_global_seed(seed: int = 42):
    """Set the global seed using the SeedManager."""
    manager = SeedManager()
    manager.set_seed(seed)

def get_seed_manager() -> SeedManager:
    """Get the SeedManager instance."""
    return SeedManager()

def sample_with_seed(data: List[Any], n: int, seed: Optional[int] = None) -> List[Any]:
    """
    Sample n items from data using a specific seed.
    
    Args:
        data: List of items to sample from.
        n: Number of items to sample.
        seed: Optional seed for reproducibility. If None, uses global seed.
        
    Returns:
        List of sampled items.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = SeedManager().get_random_state()
    
    return rng.sample(data, min(n, len(data)))

def get_random_state() -> random.Random:
    """Get the current random state."""
    return SeedManager().get_random_state()

def set_random_state(seed: int):
    """Set the random state."""
    set_global_seed(seed)

def main():
    """Test seed management."""
    set_global_seed(123)
    print(f"Seed: {get_seed_manager().get_seed()}")
    print(f"Random sample: {sample_with_seed([1,2,3,4,5], 3)}")
    # Reset seed
    set_global_seed(123)
    print(f"Random sample again: {sample_with_seed([1,2,3,4,5], 3)}")

if __name__ == "__main__":
    main()
