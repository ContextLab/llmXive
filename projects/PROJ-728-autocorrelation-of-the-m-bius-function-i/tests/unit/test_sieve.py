"""
Unit tests for the Möbius sieve implementation.

These tests verify that the linear-time sieve correctly computes the
Möbius function values for a few well‑known arguments:
    μ(1) =  1
    μ(2) = -1
    μ(4) =  0
The test also checks that the returned NumPy array has the expected
``int8`` dtype and that the dummy element at index 0 is zero.
"""

import numpy as np
import pytest

# The sieve implementation lives in ``code/sieve.py`` and exposes
# ``compute_mobius`` as a public function.
from code.sieve import compute_mobius

@pytest.fixture(scope="module")
def mobius_array():
    """
    Compute the Möbius array for a small N (≥ 4) once per test session.
    """
    N = 10  # small enough for fast execution but includes the values we test
    return compute_mobius(N)

def test_array_shape_and_dtype(mobius_array):
    """The array should have length N+1 and dtype int8."""
    assert isinstance(mobius_array, np.ndarray)
    # Length should be N+1 (including dummy index 0)
    assert mobius_array.shape == (11,)
    assert mobius_array.dtype == np.int8

def test_dummy_zero_at_index_zero(mobius_array):
    """Index 0 is unused in the mathematical definition and must be 0."""
    assert mobius_array[0] == 0

@pytest.mark.parametrize(
    "n,expected",
    [
        (1, 1),   # μ(1) = 1
        (2, -1),  # μ(2) = -1 (prime)
        (4, 0),   # μ(4) = 0 (square factor)
    ],
)
def test_known_mobius_values(mobius_array, n, expected):
    """Check that known values of the Möbius function are correct."""
    assert int(mobius_array[n]) == expected