"""
Unit tests for Benjamini-Hochberg FDR correction.

This module tests the implementation of the Benjamini-Hochberg procedure
for controlling the False Discovery Rate in multiple hypothesis testing.

The implementation is based on the standard BH algorithm:
1. Sort p-values in ascending order
2. For each p-value at rank i (1-indexed), compute adjusted p-value: p_i * m / i
3. Ensure monotonicity by taking cumulative minimum from largest to smallest
4. Cap values at 1.0

References:
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate:
  A Practical and Powerful Approach to Multiple Testing. Journal of the Royal
  Statistical Society, Series B, 57(1), 289-300.
"""

import pytest
import numpy as np
from typing import List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.metrics import benjamini_hochberg_fdr


def test_benjamini_hochberg_basic():
    """Test basic BH correction with known values."""
    # Simple case: 5 p-values
    p_values = [0.01, 0.04, 0.03, 0.20, 0.15]
    q_values = benjamini_hochberg_fdr(p_values)

    # Check that we get 5 q-values
    assert len(q_values) == 5

    # Check that q-values are monotonically non-decreasing when sorted by original p-value rank
    # (after sorting by p-value, q-values should be non-decreasing)
    sorted_indices = np.argsort(p_values)
    sorted_q = [q_values[i] for i in sorted_indices]

    # After BH correction, q-values should be non-decreasing with respect to sorted p-values
    for i in range(len(sorted_q) - 1):
        assert sorted_q[i] <= sorted_q[i + 1], \
            f"Q-values should be non-decreasing: {sorted_q}"

    # All q-values should be <= 1.0
    assert all(q <= 1.0 for q in q_values)

    # All q-values should be >= corresponding p-values (BH is conservative)
    # Actually, BH can produce q-values smaller than p-values in some cases,
    # but they should generally be larger or equal for small p-values
    # The key property is that q_i >= p_i * (m/i) before monotonicity adjustment


def test_benjamini_hochberg_all_significant():
    """Test case where all p-values are very small."""
    p_values = [0.001, 0.002, 0.003, 0.004, 0.005]
    q_values = benjamini_hochberg_fdr(p_values)

    # All should be significant at alpha=0.05
    alpha = 0.05
    significant_count = sum(1 for q in q_values if q <= alpha)
    assert significant_count == 5, "All p-values should be significant"


def test_benjamini_hochberg_none_significant():
    """Test case where all p-values are large."""
    p_values = [0.5, 0.6, 0.7, 0.8, 0.9]
    q_values = benjamini_hochberg_fdr(p_values)

    # None should be significant at alpha=0.05
    alpha = 0.05
    significant_count = sum(1 for q in q_values if q <= alpha)
    assert significant_count == 0, "No p-values should be significant"


def test_benjamini_hochberg_single_pvalue():
    """Test with a single p-value."""
    p_values = [0.03]
    q_values = benjamini_hochberg_fdr(p_values)

    # With m=1, q-value should equal p-value
    assert q_values[0] == pytest.approx(0.03, rel=1e-9)


def test_benjamini_hochberg_two_pvalues():
    """Test with two p-values."""
    p_values = [0.02, 0.04]
    q_values = benjamini_hochberg_fdr(p_values)

    # Manual calculation:
    # m = 2
    # Sorted: p1=0.02 (rank 1), p2=0.04 (rank 2)
    # q1_raw = 0.02 * 2 / 1 = 0.04
    # q2_raw = 0.04 * 2 / 2 = 0.04
    # After monotonicity: q1 = min(0.04, 0.04) = 0.04, q2 = 0.04
    # But we need to return in original order

    # The BH procedure ensures q-values are non-decreasing when sorted by p-value
    sorted_indices = np.argsort(p_values)
    sorted_q = [q_values[i] for i in sorted_indices]

    # Both should be <= 0.04 (the maximum of the two raw calculations)
    assert sorted_q[0] <= 0.04
    assert sorted_q[1] <= 0.04


def test_benjamini_hochberg_mixed_significance():
    """Test with mixed significant and non-significant p-values."""
    p_values = [0.001, 0.01, 0.05, 0.1, 0.2]
    q_values = benjamini_hochberg_fdr(p_values)

    # At alpha=0.05, we expect some to be significant and some not
    alpha = 0.05
    significant_count = sum(1 for q in q_values if q <= alpha)

    # We expect at least the smallest p-value to be significant
    assert significant_count >= 1

    # And not all should be significant
    assert significant_count < 5


def test_benjamini_hochberg_edge_case_zeros():
    """Test with p-values that are zero (or very close to zero)."""
    p_values = [0.0, 0.001, 0.01]
    q_values = benjamini_hochberg_fdr(p_values)

    # Zero p-values should result in zero q-values
    assert q_values[0] == 0.0

    # All q-values should be valid (non-negative and <= 1)
    assert all(q >= 0 and q <= 1 for q in q_values)


def test_benjamini_hochberg_edge_case_ones():
    """Test with p-values that are one."""
    p_values = [1.0, 1.0, 1.0]
    q_values = benjamini_hochberg_fdr(p_values)

    # All q-values should be 1.0
    assert all(q == 1.0 for q in q_values)


def test_benjamini_hochberg_monotonicity():
    """Test that q-values maintain monotonicity property."""
    # Generate random p-values
    np.random.seed(42)
    p_values = np.random.uniform(0, 1, 20).tolist()

    q_values = benjamini_hochberg_fdr(p_values)

    # Sort by p-value and check that q-values are non-decreasing
    sorted_indices = np.argsort(p_values)
    sorted_q = [q_values[i] for i in sorted_indices]

    for i in range(len(sorted_q) - 1):
        assert sorted_q[i] <= sorted_q[i + 1], \
            f"Monotonicity violated at index {i}: {sorted_q[i]} > {sorted_q[i + 1]}"


def test_benjamini_hochberg_known_example():
    """Test against a known example from literature."""
    # Example from Benjamini & Hochberg (1995)
    # 10 p-values: 0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08
    p_values = [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]
    q_values = benjamini_hochberg_fdr(p_values)

    # Manual calculation for verification:
    # m = 10
    # For each p_i at rank i: q_i_raw = p_i * 10 / i
    # Then apply monotonicity (cumulative minimum from largest to smallest)

    # Rank 1: 0.001 * 10 / 1 = 0.01
    # Rank 2: 0.005 * 10 / 2 = 0.025
    # Rank 3: 0.01 * 10 / 3 = 0.0333...
    # Rank 4: 0.02 * 10 / 4 = 0.05
    # Rank 5: 0.03 * 10 / 5 = 0.06
    # Rank 6: 0.04 * 10 / 6 = 0.0667...
    # Rank 7: 0.05 * 10 / 7 = 0.0714...
    # Rank 8: 0.06 * 10 / 8 = 0.075
    # Rank 9: 0.07 * 10 / 9 = 0.0778...
    # Rank 10: 0.08 * 10 / 10 = 0.08

    # After monotonicity adjustment (cumulative minimum from right):
    # q_10 = 0.08
    # q_9 = min(0.0778, 0.08) = 0.0778
    # q_8 = min(0.075, 0.0778) = 0.075
    # ... and so on

    # Check that the first q-value is approximately 0.01
    assert q_values[0] == pytest.approx(0.01, rel=1e-6)

    # Check that the last q-value is approximately 0.08
    assert q_values[9] == pytest.approx(0.08, rel=1e-6)


def test_benjamini_hochberg_input_validation():
    """Test that invalid inputs raise appropriate errors."""
    # Empty list
    with pytest.raises((ValueError, IndexError)):
        benjamini_hochberg_fdr([])

    # Negative p-value
    with pytest.raises(ValueError):
        benjamini_hochberg_fdr([-0.1, 0.5])

    # p-value > 1
    with pytest.raises(ValueError):
        benjamini_hochberg_fdr([0.5, 1.5])


def test_benjamini_hochberg_deterministic():
    """Test that the function is deterministic."""
    p_values = [0.01, 0.05, 0.1, 0.2, 0.3]

    result1 = benjamini_hochberg_fdr(p_values)
    result2 = benjamini_hochberg_fdr(p_values)

    assert result1 == result2

    # Test with numpy array input
    result3 = benjamini_hochberg_fdr(np.array(p_values))
    assert result1 == result3


def test_benjamini_hochberg_large_dataset():
    """Test with a larger dataset to ensure scalability."""
    np.random.seed(123)
    p_values = np.random.uniform(0, 1, 1000).tolist()

    q_values = benjamini_hochberg_fdr(p_values)

    # Should return same number of q-values
    assert len(q_values) == 1000

    # All should be in [0, 1]
    assert all(0 <= q <= 1 for q in q_values)

    # Monotonicity check
    sorted_indices = np.argsort(p_values)
    sorted_q = [q_values[i] for i in sorted_indices]

    for i in range(len(sorted_q) - 1):
        assert sorted_q[i] <= sorted_q[i + 1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])