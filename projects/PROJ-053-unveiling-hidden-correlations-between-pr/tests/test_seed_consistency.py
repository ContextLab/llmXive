"""
Test that the global random seeds are set consistently.

The test imports the ``set_global_seeds`` function from the project's
``io_utils`` module, resets the RNG state, generates a small sample of
random numbers from both ``numpy`` and the built‑in ``random`` module,
resets the seeds again, and verifies that the newly generated numbers
match the previously generated ones. This demonstrates that the seed
configuration is deterministic across runs.
"""

import importlib

import numpy as np
import random

from code.utils.io_utils import set_global_seeds

def _sample_random_values():
    """Generate a short deterministic sequence of random values."""
    # Generate three floats from numpy and three from the built‑in random.
    np_vals = np.random.rand(3).tolist()
    py_vals = [random.random() for _ in range(3)]
    return np_vals, py_vals

def test_global_seed_consistency():
    # First sampling after an explicit seed reset.
    set_global_seeds()  # Reset to the configured seed (42)
    np_vals_first, py_vals_first = _sample_random_values()

    # Reset the seeds again to the same value.
    set_global_seeds()
    np_vals_second, py_vals_second = _sample_random_values()

    # The two sequences must be identical.
    assert np_vals_first == np_vals_second, "NumPy random sequence is not repeatable"
    assert py_vals_first == py_vals_second, "Python random sequence is not repeatable"