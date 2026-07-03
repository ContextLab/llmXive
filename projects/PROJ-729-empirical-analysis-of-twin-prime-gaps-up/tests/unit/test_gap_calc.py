"""
Unit tests for gap calculation logic.

This module verifies the normalized gap formula:
    normalized_gap = delta / log(p)
where delta = p_next - p.
"""

import math
import pytest


def test_normalized_gap_formula():
    """
    Verify the normalized gap calculation for a specific twin prime pair.

    Input: p = 3, p_next = 5 (the first twin prime pair)
    Expected:
        delta = 5 - 3 = 2
        log(p) = log(3)
        normalized_gap = 2 / log(3) ≈ 1.820478...

    The task requires asserting the result is within 1e-4 of 1.8205.
    """
    p = 3
    p_next = 5

    delta = p_next - p
    log_p = math.log(p)
    normalized_gap = delta / log_p

    expected = 1.8205
    tolerance = 1e-4

    assert abs(normalized_gap - expected) < tolerance, (
        f"Expected normalized_gap ≈ {expected} ± {tolerance}, "
        f"but got {normalized_gap}"
    )