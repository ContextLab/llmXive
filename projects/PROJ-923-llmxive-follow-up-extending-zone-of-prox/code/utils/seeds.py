"""
Seed management utilities.
Ensures deterministic behavior for all random number generators.
"""
import random
import os
from typing import Optional
import numpy as np

def set_global_seed(seed: int):
    """Sets seed for random, numpy, and os.environ if needed."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed(config_seed: Optional[int] = None) -> int:
    """Retrieves seed from config or environment, defaults to 42."""
    if config_seed is not None:
        return config_seed
    env_seed = os.environ.get('SEED')
    if env_seed:
        return int(env_seed)
    return 42

def reset_to_default():
    """Resets seeds to default (42)."""
    set_global_seed(42)

def get_seed_or_default(seed: Optional[int] = None) -> int:
    """Returns seed or default if None."""
    return seed if seed is not None else 42

def generate_seed() -> int:
    """Generates a new random seed."""
    return random.randint(0, 2**32 - 1)

def seed_context(seed: int):
    """Context manager for temporary seed setting."""
    class SeedContext:
        def __enter__(self):
            self.old_state = random.getstate()
            self.old_np_state = np.random.get_state()
            set_global_seed(seed)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            random.setstate(self.old_state)
            np.random.set_state(self.old_np_state)
    return SeedContext()

def initialize_project_seed(seed: int):
    """Initializes all seeds for the project run."""
    set_global_seed(seed)
