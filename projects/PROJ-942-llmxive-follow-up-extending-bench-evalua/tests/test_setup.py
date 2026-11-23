"""
Test suite for the initial project setup (T000).

The tests verify two things:
1. The ``datasets`` package (declared in ``requirements.txt``) can be imported.
2. The seed initialisation produces a deterministic NumPy random value.
"""

import importlib
import numpy as np

def test_datasets_importable():
    """
    Ensure that the ``datasets`` library is available.
    """
    datasets = importlib.import_module("datasets")
    assert hasattr(datasets, "__version__"), "datasets package should expose a __version__ attribute"

def test_seed_determinism():
    """
    After calling ``utils.seed.set_seeds`` the first NumPy random value must be
    reproducible and match the reference value obtained with seed=42.
    """
    # Import the seed helper and (re)initialise the seeds.
    from utils.seed import set_seeds

    set_seeds(42)
    # The first call to ``np.random.rand()`` after seeding with 42 yields this constant.
    first_val = np.random.rand()
    expected = 0.3745401188473625
    assert abs(first_val - expected) < 1e-12, f"Expected {expected}, got {first_val}"