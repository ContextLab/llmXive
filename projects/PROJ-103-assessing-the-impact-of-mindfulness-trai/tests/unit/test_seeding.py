"""
Unit test for the seeding utilities defined in ``src.utils.seeding``.
The test ensures that the deterministic verification helper works by
running a simple NumPy operation twice under the same seed and checking
that the hashed outputs are identical.
"""

import numpy as np
import pytest

from src.utils.seeding import verify_determinism, set_all_seeds, DEFAULT_SEED


def _trivial_numpy_op():
    """Return a small NumPy array – used for deterministic testing."""
    return np.arange(5) * 2.5


def test_seeding_is_deterministic():
    # The helper should return True when the function produces identical
    # results under the same seed.
    set_all_seeds(DEFAULT_SEED)
    assert verify_determinism(_trivial_numpy_op, seed=DEFAULT_SEED, iterations=2) is True


def test_verify_determinism_raises_on_nondeterministic():
    # Create a function that deliberately changes output between calls.
    counter = {"i": 0}

    def nondet():
        counter["i"] += 1
        return np.array([counter["i"]])

    # The verification should raise a RuntimeError because the hashes differ.
    with pytest.raises(RuntimeError):
        verify_determinism(nondet, seed=DEFAULT_SEED, iterations=2)