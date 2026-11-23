"""
Test to verify that the global random seeds are set consistently
across runs via ``code.utils.io_utils``.
"""

import importlib
import sys

import numpy as np
import random


def test_seed_consistency():
    """
    Ensure that after importing ``code.utils.io_utils`` the first
    random draws from ``numpy`` and ``random`` are deterministic
    and match the expected values for seed 42.
    """
    # Reload the module to guarantee that the seed-setting code runs
    module_name = "code.utils.io_utils"
    if module_name in sys.modules:
        del sys.modules[module_name]
    importlib.import_module(module_name)

    # Expected values after setting the seed to 42
    expected_numpy = 0.3745401188473625  # np.random.rand() first value
    expected_random = 0.6394267984578837  # random.random() first value

    # Draw a single random number from each library
    np_val = np.random.rand()
    rand_val = random.random()

    # Assertions
    assert np.isclose(np_val, expected_numpy, atol=1e-12), (
        f"Numpy random value {np_val} does not match expected {expected_numpy}"
    )
    assert abs(rand_val - expected_random) < 1e-12, (
        f"Random module value {rand_val} does not match expected {expected_random}"
    )