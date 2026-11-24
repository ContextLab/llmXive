"""
Minimal configuration utilities required by the predictive modeling script.
Only the random‑seed helper is needed for reproducibility.
"""

import random
import numpy as np

def set_random_seed(seed: int = 42):
    """
    Set the global random seed for Python's random module,
    NumPy and any other library that respects NumPy's RNG.
    """
    random.seed(seed)
    np.random.seed(seed)