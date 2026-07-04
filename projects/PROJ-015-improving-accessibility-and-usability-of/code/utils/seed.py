import os
import random
from typing import Optional, Union
import numpy as np

def get_seed_from_env() -> int:
    seed_str = os.getenv("PYTHONHASHSEED", "42")
    try:
        return int(seed_str)
    except ValueError:
        return 42

def set_seed(seed: Optional[int] = None):
    if seed is None:
        seed = get_seed_from_env()
    random.seed(seed)
    np.random.seed(seed)

def seeded_generator(seed: Optional[int] = None):
    set_seed(seed)
    return random

def seeded_numpy_generator(seed: Optional[int] = None):
    set_seed(seed)
    return np.random

def main():
    print("Seed module loaded.")
