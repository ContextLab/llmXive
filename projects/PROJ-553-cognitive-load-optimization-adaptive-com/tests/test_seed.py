"""
Unit test for the ``code.seed`` module.

The test verifies that calling ``set_seed()`` produces deterministic
outputs from both the ``random`` and ``numpy`` random generators.
"""

import importlib

import numpy as np
import random

# Import the seed module fresh for each test run
seed_module = importlib.import_module("code.seed")

def _generate_numbers():
    """Generate a pair of random numbers from ``random`` and ``numpy``."""
    py_rand = random.random()
    np_rand = np.random.rand()
    return py_rand, np_rand

def test_repeatability():
    # First run
    seed_module.set_seed()
    first_py, first_np = _generate_numbers()

    # Reset the seed and generate again
    seed_module.set_seed()
    second_py, second_np = _generate_numbers()

    assert first_py == second_py, "Python random numbers differ after reseeding"
    assert first_np == second_np, "NumPy random numbers differ after reseeding"

# Ensure the module can be reloaded without side‑effects
def test_custom_seed():
    custom = 12345
    seed_module.set_seed(custom)
    a_py, a_np = _generate_numbers()

    seed_module.set_seed(custom)
    b_py, b_np = _generate_numbers()

    assert a_py == b_py, "Custom seed did not produce repeatable Python random numbers"
    assert a_np == b_np, "Custom seed did not produce repeatable NumPy random numbers"