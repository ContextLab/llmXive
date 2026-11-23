"""
Seeding Utilities.

Provides consistent random seeding for reproducibility.
"""

import os
import random
from typing import Optional, Union
import numpy as np

def get_seed_from_env() -> int:
    """Get seed from environment variable or default."""
    return int(os.environ.get("RESEARCH_SEED", "42"))

def set_seed(seed: Optional[int] = None):
    """Set seeds for random, numpy, and python hash."""
    if seed is None:
        seed = get_seed_from_env()
    
    random.seed(seed)
    np.random.seed(seed)
    # Python 3.3+ hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)

def seeded_generator(seed: Optional[int] = None):
    """Context manager for seeded random operations."""
    if seed is None:
        seed = get_seed_from_env()
    state = random.getstate()
    random.seed(seed)
    try:
        yield
    finally:
        random.setstate(state)

def seeded_numpy_generator(seed: Optional[int] = None):
    """Context manager for seeded numpy operations."""
    if seed is None:
        seed = get_seed_from_env()
    state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(state)

def main():
    """Test seeding."""
    set_seed(42)
    print(f"Random: {random.random()}")
    print(f"Numpy: {np.random.random()}")

if __name__ == "__main__":
    main()
