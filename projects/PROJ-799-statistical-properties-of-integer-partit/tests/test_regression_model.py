import pytest
import json
import os
import sys
import numpy as np

# Ensure the code directory is in the path for imports
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from regression_model import benjamini_hochberg

class TestBenjaminiHochberg:
    """
    Test suite for the Benjamini-Hochberg correction implementation.
    This test verifies that p-values are adjusted correctly in isolation
    using synthetic p-values, independent of full model output.
    """

    def test_bh_correction_increasing_order(self):
        """
        Verify that the Benjamini-Hochberg procedure returns adjusted p-values
        that are monotonically non-decreasing with respect to the original p-value ranks.
        
        The BH procedure ensures that if p_i <= p_j, then q_i <= q_j.
        """
        # Synthetic p-values in arbitrary order
        raw_p_values = [0.01, 0.04, 0.03, 0.005, 0.06, 0.02]
        m = len(raw_p_values)
        
        adjusted = benjamini_hochberg(raw_p_values)
        
        # Sort original p-values to check rank correspondence
        sorted_indices = sorted(range(m), key=lambda k: raw_p_values[k])
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        # Check monotonicity: adjusted p-values should be non-decreasing
        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i+1], \
                f"BH correction failed monotonicity: {sorted_adjusted[i]} > {sorted_adjusted[i+1]}"

    def test_bh_correction_known_values(self):
        """
        Test against a known example where we can manually calculate the expected result.
        
        Example: raw p-values [0.001, 0.004, 0.03, 0.05] with m=4, alpha=0.05.
        Expected adjusted values (q_i = p_i * m / i, then min(q_j, q_{j+1}) for j > i):
        1. Sort: 0.001 (rank 1), 0.004 (rank 2), 0.03 (rank 3), 0.05 (rank 4)
        2. Calculate raw q:
           - Rank 1: 0.001 * 4 / 1 = 0.004
           - Rank 2: 0.004 * 4 / 2 = 0.008
           - Rank 3: 0.03 * 4 / 3 = 0.04
           - Rank 4: 0.05 * 4 / 4 = 0.05
        3. Enforce monotonicity from bottom up:
           - q[4] = 0.05
           - q[3] = min(0.04, 0.05) = 0.04
           - q[2] = min(0.008, 0.04) = 0.008
           - q[1] = min(0.004, 0.008) = 0.004
        Result: [0.004, 0.008, 0.04, 0.05]
        """
        raw_p_values = [0.001, 0.004, 0.03, 0.05]
        expected_adjusted = [0.004, 0.008, 0.04, 0.05]
        
        adjusted = benjamini_hochberg(raw_p_values)
        
        # The function returns adjusted values in the same order as input
        # We need to map back to original order
        # Input order: 0.001 (rank 1), 0.004 (rank 2), 0.03 (rank 3), 0.05 (rank 4)
        # So adjusted should be [0.004, 0.008, 0.04, 0.05]
        
        for i, (obs, exp) in enumerate(zip(adjusted, expected_adjusted)):
            assert np.isclose(obs, exp, rtol=1e-5), \
                f"Expected {exp} at index {i}, got {obs}"

    def test_bh_correction_all_significant(self):
        """
        Test case where all p-values are small enough to be significant after correction.
        """
        raw_p_values = [0.001, 0.002, 0.003, 0.004]
        alpha = 0.05
        
        adjusted = benjamini_hochberg(raw_p_values)
        
        # All adjusted p-values should be <= alpha
        for p_adj in adjusted:
            assert p_adj <= alpha, f"Adjusted p-value {p_adj} exceeds alpha {alpha}"

    def test_bh_correction_all_insignificant(self):
        """
        Test case where all p-values are large and remain insignificant.
        """
        raw_p_values = [0.5, 0.6, 0.7, 0.8]
        alpha = 0.05
        
        adjusted = benjamini_hochberg(raw_p_values)
        
        # All adjusted p-values should be > alpha (or very close to 1)
        for p_adj in adjusted:
            assert p_adj > alpha, f"Adjusted p-value {p_adj} is unexpectedly significant"

    def test_bh_correction_single_value(self):
        """
        Edge case: single p-value.
        """
        raw_p_values = [0.03]
        adjusted = benjamini_hochberg(raw_p_values)
        
        # For m=1, q = p * 1 / 1 = p
        assert np.isclose(adjusted[0], 0.03), \
            f"Single p-value correction failed: expected 0.03, got {adjusted[0]}"

    def test_bh_correction_empty_list(self):
        """
        Edge case: empty list of p-values.
        """
        raw_p_values = []
        adjusted = benjamini_hochberg(raw_p_values)
        
        assert adjusted == [], "Empty list should return empty list"

    def test_bh_correction_duplicate_values(self):
        """
        Test handling of duplicate p-values.
        """
        raw_p_values = [0.01, 0.01, 0.01, 0.02]
        adjusted = benjamini_hochberg(raw_p_values)
        
        # Check that all adjusted values are <= 1.0
        for p_adj in adjusted:
            assert 0.0 <= p_adj <= 1.0, f"Adjusted p-value {p_adj} out of bounds"

    def test_bh_correction_returns_same_length(self):
        """
        Verify the output list has the same length as input.
        """
        raw_p_values = [0.01, 0.05, 0.1, 0.2, 0.3]
        adjusted = benjamini_hochberg(raw_p_values)
        
        assert len(adjusted) == len(raw_p_values), \
            f"Length mismatch: input {len(raw_p_values)}, output {len(adjusted)}"

    def test_bh_correction_clamped_to_one(self):
        """
        Verify that adjusted p-values are clamped to 1.0 if they exceed it.
        """
        raw_p_values = [0.9, 0.95, 0.99]
        adjusted = benjamini_hochberg(raw_p_values)
        
        for p_adj in adjusted:
            assert p_adj <= 1.0, f"Adjusted p-value {p_adj} exceeds 1.0"