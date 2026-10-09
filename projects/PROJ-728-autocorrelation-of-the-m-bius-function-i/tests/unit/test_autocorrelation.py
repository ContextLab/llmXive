"""
Unit tests for ``code.autocorrelation``.
"""

from pathlib import Path

import numpy as np
import pytest

# Import the functions from the module we just created.
from autocorrelation import compute_autocorrelation, _compute_autocorrelation_loop

# Load the real Möbius array once for all tests.
MOBIUS_PATH = Path("data/raw/mobius_array.npy")
MOBIUS = np.load(MOBIUS_PATH)


@pytest.mark.parametrize(
    "start,L,h",
    [
        (44622, 1000, 1),   # first window for L=1000 (matches demo)
        (886890, 1000, 5),  # a different lag to ensure generality
        (249926, 10000, 2), # larger window length
    ],
)
def test_autocorrelation_consistency(start: int, L: int, h: int) -> None:
    """The fast and slow implementations must agree."""
    fast = compute_autocorrelation(MOBIUS, start, L, h)
    slow = _compute_autocorrelation_loop(MOBIUS, start, L, h)
    assert np.isclose(fast, slow, atol=1e-12)

def test_invalid_lag_raises() -> None:
    """Lag equal to or larger than L should raise a ValueError."""
    with pytest.raises(ValueError):
        compute_autocorrelation(MOBIUS, start=0, L=10, h=10)
    with pytest.raises(ValueError):
        compute_autocorrelation(MOBIUS, start=0, L=10, h=11)