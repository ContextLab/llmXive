import random
import numpy as np
from utils.seed import set_seed

def test_seed_reproducibility():
    """
    After setting a fixed seed, the first values drawn from ``random`` and
    ``numpy`` must match the known reference values for seed 42.
    """
    set_seed(42)
    assert random.random() == 0.6394267984578837
    assert np.random.rand() == 0.3745401188473625