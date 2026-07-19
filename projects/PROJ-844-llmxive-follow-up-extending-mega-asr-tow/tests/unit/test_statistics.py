"""
Unit tests for statistical correction logic in code/statistics.py.

Specifically verifies Bonferroni correction factor application based on the
exact number of interaction terms tested to prevent artificial p-value inflation.
"""
import pytest
import math
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.statistics import apply_bonferroni_correction, apply_fdr_correction


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction implementation."""

    def test_bonferroni_single_test(self):
        """Verify correction when only 1 test is performed."""
        raw_p_value = 0.05
        num_tests = 1
        
        corrected = apply_bonferroni_correction(raw_p_value, num_tests)
        
        # For 1 test, corrected should equal raw
        assert corrected == raw_p_value
        assert math.isclose(corrected, 0.05)

    def test_bonferroni_interaction_terms(self):
        """
        Verify Bonferroni correction factor is correctly applied based on
        the exact number of interaction terms.
        
        Context: US3 generates 3 interaction terms (SNR×RT60, SNR², RT60²).
        If we test these 3 terms, the correction factor must be 3.
        """
        raw_p_value = 0.03
        num_interaction_terms = 3
        
        corrected = apply_bonferroni_correction(raw_p_value, num_interaction_terms)
        
        # Expected: 0.03 * 3 = 0.09
        expected = raw_p_value * num_interaction_terms
        
        assert math.isclose(corrected, expected)
        assert corrected == 0.09

    def test_bonferroni_caps_at_one(self):
        """Verify that corrected p-values are capped at 1.0."""
        raw_p_value = 0.5
        num_tests = 3
        
        corrected = apply_bonferroni_correction(raw_p_value, num_tests)
        
        # 0.5 * 3 = 1.5, but should be capped at 1.0
        assert corrected == 1.0

    def test_bonferroni_no_inflation(self):
        """
        Ensure p-values are not artificially inflated.
        
        The correction should strictly be: corrected = min(raw * k, 1.0)
        It should never be less than raw (unless raw > 1 which is invalid).
        """
        raw_p_value = 0.01
        num_tests = 5
        
        corrected = apply_bonferroni_correction(raw_p_value, num_tests)
        
        # Corrected must be >= raw
        assert corrected >= raw_p_value
        
        # Must be exactly raw * num_tests (unless capped)
        expected = min(raw_p_value * num_tests, 1.0)
        assert math.isclose(corrected, expected)

    def test_bonferroni_zero_tests_raises(self):
        """Verify that zero tests raises a ValueError."""
        with pytest.raises(ValueError, match="Number of tests must be positive"):
            apply_bonferroni_correction(0.05, 0)

    def test_bonferroni_negative_p_raises(self):
        """Verify that negative p-values raise a ValueError."""
        with pytest.raises(ValueError, match="P-value must be between 0 and 1"):
            apply_bonferroni_correction(-0.1, 3)

    def test_bonferroni_p_greater_than_one_raises(self):
        """Verify that p-values > 1 raise a ValueError."""
        with pytest.raises(ValueError, match="P-value must be between 0 and 1"):
            apply_bonferroni_correction(1.5, 3)

    def test_bonferroni_large_number_of_tests(self):
        """Test with a large number of interaction terms (e.g., polynomial expansion)."""
        raw_p_value = 0.001
        num_tests = 100
        
        corrected = apply_bonferroni_correction(raw_p_value, num_tests)
        
        # 0.001 * 100 = 0.1
        assert math.isclose(corrected, 0.1)

    def test_bonferroni_very_small_p_value(self):
        """Test with a very small raw p-value."""
        raw_p_value = 1e-10
        num_tests = 10
        
        corrected = apply_bonferroni_correction(raw_p_value, num_tests)
        
        # 1e-10 * 10 = 1e-9
        assert math.isclose(corrected, 1e-9)


class TestFDRCorrection:
    """Tests for the Benjamini-Hochberg FDR correction implementation."""

    def test_fdr_simple_case(self):
        """Test FDR correction with a simple list of p-values."""
        p_values = [0.01, 0.04, 0.03, 0.10, 0.05]
        
        corrected = apply_fdr_correction(p_values)
        
        # The corrected values should be non-decreasing when sorted by original index
        # and should generally be larger than or equal to raw p-values
        assert len(corrected) == len(p_values)
        
        # Check that all corrected values are <= 1.0
        assert all(p <= 1.0 for p in corrected)

    def test_fdr_single_value(self):
        """Test FDR with a single p-value."""
        p_values = [0.05]
        
        corrected = apply_fdr_correction(p_values)
        
        # For a single value, BH correction is: p * n / rank = 0.05 * 1 / 1 = 0.05
        assert math.isclose(corrected[0], 0.05)

    def test_fdr_empty_list_raises(self):
        """Verify that an empty list raises a ValueError."""
        with pytest.raises(ValueError, match="P-values list cannot be empty"):
            apply_fdr_correction([])

    def test_fdr_monotonicity(self):
        """
        Verify that the BH procedure produces monotonic adjusted p-values
        (i.e., adjusted p-values are non-decreasing with respect to the rank).
        """
        # Unsorted p-values
        p_values = [0.05, 0.01, 0.03, 0.02]
        
        corrected = apply_fdr_correction(p_values)
        
        # The BH procedure ensures that adjusted p-values are monotonic
        # when sorted by original p-value. We verify the logic by checking
        # that the algorithm doesn't produce decreasing adjusted values
        # for increasing raw p-values in the sorted sequence.
        
        # Sort indices by raw p-values
        sorted_indices = sorted(range(len(p_values)), key=lambda k: p_values[k])
        sorted_raw = [p_values[i] for i in sorted_indices]
        sorted_corrected = [corrected[i] for i in sorted_indices]
        
        # Ensure monotonicity: corrected[i] <= corrected[i+1] for sorted list
        for i in range(len(sorted_corrected) - 1):
            assert sorted_corrected[i] <= sorted_corrected[i+1] + 1e-9  # tolerance for float errors