"""
Seed management for reproducible experiments.
Manages random seeds for all sampling and statistical resampling.
"""
import random
import numpy as np
import os
from typing import Optional, List, Any

class SeedManager:
    """Manages global random seeds for reproducibility."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self._set_seeds()
    
    def _set_seeds(self):
        """Sets seeds for random, numpy, and os.environ (if applicable)."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        # Optional: Set PYTHONHASHSEED if needed for hash reproducibility
        # os.environ['PYTHONHASHSEED'] = str(self.seed)
    
    def set_seed(self, seed: int):
        """Updates the global seed."""
        self.seed = seed
        self._set_seeds()

_global_seed_manager = SeedManager(42)

def set_global_seed(seed: int = 42):
    """Sets the global seed for all random number generators."""
    _global_seed_manager.set_seed(seed)

def get_seed_manager() -> SeedManager:
    """Returns the global seed manager instance."""
    return _global_seed_manager

def sample_with_seed(data: List[Any], n: int, seed: Optional[int] = None) -> List[Any]:
    """Samples n items from data using a specific seed."""
    if seed is not None:
        random.seed(seed)
    return random.sample(data, n)

def get_random_state() -> Any:
    """Returns the current random state."""
    return random.getstate()

def set_random_state(state: Any):
    """Sets the random state."""
    random.setstate(state)

def main():
    """CLI for testing seed functionality."""
    print(f"Default seed: {_global_seed_manager.seed}")
    set_global_seed(123)
    print(f"New seed: {_global_seed_manager.seed}")
    print(f"Random number: {random.random()}")

if __name__ == "__main__":
    main()