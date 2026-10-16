"""
Unit tests for the seeding utilities.

The test verifies that a simple NumPy‑based random operation is fully
deterministic when the global seed is fixed and that the helper
``verify_determinism`` correctly detects this.
"""

import numpy as np
from code.utils.seeding import set_all_seeds, verify_determinism, DEFAULT_SEED


def dummy_numpy_operation():
    """Return a small NumPy array of random numbers."""
    return np.random.rand(5)


def test_deterministic_numpy_operation():
    # Ensure the global seed is set to the default before each run.
    set_all_seeds(DEFAULT_SEED)

    # ``verify_determinism`` will run the function twice (default
    # ``iterations=2``) and raise if the outputs differ.
    assert verify_determinism(dummy_numpy_operation, seed=DEFAULT_SEED) is True


def test_get_seed_constant():
    # The constant ``DEFAULT_SEED`` should match the value returned by
    # ``get_seed`` (exposed via the wrapper in ``code.utils.seeding``).
    from code.utils.seeding import get_seed

    assert get_seed() == DEFAULT_SEED