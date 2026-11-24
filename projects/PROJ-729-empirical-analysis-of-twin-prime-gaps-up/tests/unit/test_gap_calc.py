"""
Unit tests for gap calculation logic.
"""
import math
import sys
import os
import pytest

# Ensure the project's ``code`` directory is on the import path.
code_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "code"))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

# Import the function that computes the normalized gap.
from generate_primes import normalized_gap

def test_normalized_gap_formula():
    """
    Verify the normalized gap formula: delta / log(p).
    Specific test case: p=3, p_next=5.
    Expected delta = 2.
    Expected normalized_gap = 2 / log(3).
    """
    p = 3
    p_next = 5
    delta = p_next - p

    # Expected value computed independently.
    expected_normalized = delta / math.log(p)

    # Actual value using the library function.
    actual_normalized = normalized_gap(p, p_next)

    # Assert with tolerance for floating point precision
    assert abs(actual_normalized - expected_normalized) < 1e-4, (
        f"Normalized gap calculation failed: {actual_normalized} != {expected_normalized}"
    )

    # Specific checks
    assert actual_normalized > 0, "Normalized gap must be positive for p > 1"
    assert math.isfinite(actual_normalized), "Normalized gap must be finite"