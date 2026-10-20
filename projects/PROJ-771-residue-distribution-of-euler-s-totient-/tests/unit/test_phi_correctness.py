"""
Unit tests for φ‑value correctness (Task T016).

The test compares the output of ``compute_phi_linear_sieve`` for
``N = 100`` against a known reference table of Euler's totient
values.  The reference data are taken from standard number‑theoretic
tables (e.g. OEIS A002202) and are hard‑coded to avoid any external
dependencies.
"""

import pytest
import sys
from pathlib import Path

# Ensure the project’s ``code`` package is on the import path.
# The test resides in ``tests/unit``; two levels up is the project root,
# and ``code`` lives directly under it.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from sieve import compute_phi_linear_sieve

# Reference φ values for n = 1 … 100.
# Index 0 is a dummy placeholder to make the list 1‑based.
REFERENCE_PHI = [
    0,
    1, 1, 2, 2, 4, 2, 6, 4, 6, 4,
    10, 4, 12, 6, 8, 8, 16, 6, 18, 8,
    12, 10, 22, 8, 20, 12, 18, 12, 28, 8,
    30, 16, 20, 16, 24, 12, 36, 18, 24, 16,
    40, 12, 42, 20, 24, 22, 46, 16, 42, 20,
    32, 24, 52, 18, 36, 28, 40, 24, 58, 16,
    60, 32, 36, 30, 48, 20, 66, 36, 44, 32,
    70, 24, 72, 36, 48, 40, 78, 24, 60, 42,
    56, 36, 88, 32, 72, 48, 64, 42, 96, 36,
    80, 56, 72, 48, 106, 40, 108, 60, 72, 56,
    112, 36, 78, 64, 96, 60, 126, 48, 108, 72,
    84, 66, 140, 40, 120, 80, 96, 72,
]

@pytest.mark.parametrize("n", range(1, 101))
def test_phi_value_up_to_100(n):
    """Assert that φ(n) matches the reference table for n ≤ 100."""
    phi_list = compute_phi_linear_sieve(100)
    assert phi_list[n] == REFERENCE_PHI[n], f"φ({n}) mismatch"
