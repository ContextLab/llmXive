"""
test_seed.py
--------------

Verifies that the deterministic seed handling produces reproducible
random numbers from Python's ``random`` module and NumPy.
"""

import random

import numpy as np

from utils.seed import set_seed


def test_seed_reproducibility():
    """
    After setting a fixed seed, the first values drawn from ``random`` and
    ``numpy`` must match the known reference values for seed 42.
    """
    set_seed(42)

    # Expected first values for seed 42
    expected_random = 0.6394267984578837
    expected_numpy = 0.3745401188473625

    assert random.random() == expected_random, "random.random() does not match expected value"
    assert np.random.rand() == expected_numpy, "np.random.rand() does not match expected value"
