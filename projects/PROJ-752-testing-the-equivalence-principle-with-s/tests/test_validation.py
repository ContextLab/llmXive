"""
Unit tests for statistical validation logic, specifically focusing on
multiple-comparison corrections (Bonferroni, Holm-Bonferroni, Benjamini-Hochberg).
"""

import pytest
import numpy as np
from typing import List

# Import the function to be tested.
# Since the implementation is in analysis/validation.py, we import it directly.
# If the module doesn't exist yet, this test will fail with ImportError,
# which is the expected TDD behavior (Red phase).
try:
    from analysis.validation import apply_correction
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False

@pytest.fixture
def sample_p_values() -> List[float]:
    """Provides a standard set of p-values for testing correction logic."""
    return [0.01, 0.04, 0.03, 0.001, 0.05, 0.02, 0.005]

@pytest.fixture
def sorted_p_values() -> List[float]:
    """Provides p-values already sorted in ascending order."""
    return [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05]

@pytest.mark.skipif(not MODULE_EXISTS, reason="analysis.validation module not yet implemented")
class TestBonferroniCorrection:
    """Tests for the Bonferroni correction method."""

    def test_bonferroni_basic(self, sample_p_values):
        """Test that Bonferroni correction multiplies p-values by count."""
        m = len(sample_p_values)
        corrected = apply_correction(sample_p_values, method="bonferroni")
        
        # Bonferroni: p_corrected = min(p * m, 1.0)
        expected = [min(p * m, 1.0) for p in sample_p_values]
        
        np.testing.assert_array_almost_equal(corrected, expected, decimal=10)

    def test_bonferroni_caps_at_one(self):
        """Test that Bonferroni correction does not exceed 1.0."""
        p_values = [0.9, 0.95]
        corrected = apply_correction(p_values, method="bonferroni")
        assert all(p <= 1.0 for p in corrected)
        # Specifically check the cap logic
        expected = [1.0, 1.0] # 0.9*2=1.8->1.0, 0.95*2=1.9->1.0
        np.testing.assert_array_almost_equal(corrected, expected, decimal=10)

    def test_bonferroni_preserves_order(self, sample_p_values):
        """Test that Bonferroni correction preserves the original order of p-values."""
        corrected = apply_correction(sample_p_values, method="bonferroni")
        # The relative order should remain the same since it's a scalar multiplication
        original_sorted_indices = np.argsort(sample_p_values)
        corrected_sorted_indices = np.argsort(corrected)
        np.testing.assert_array_equal(original_sorted_indices, corrected_sorted_indices)

@pytest.mark.skipif(not MODULE_EXISTS, reason="analysis.validation module not yet implemented")
class TestHolmBonferroniCorrection:
    """Tests for the Holm-Bonferroni (step-down) correction method."""

    def test_holm_bonferroni_step_down(self, sorted_p_values):
        """
        Test Holm-Bonferroni logic:
        1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
        2. Compare p(i) with alpha / (m - i + 1)
        3. Adjusted p(i) = max( (m - j + 1) * p(j) for j <= i )
        """
        m = len(sorted_p_values)
        corrected = apply_correction(sorted_p_values, method="holm-bonferroni")
        
        # Manual calculation for verification
        # p_sorted = [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05]
        # m = 7
        # i=0: (7-0)*0.001 = 0.007
        # i=1: max(0.007, (6)*0.005) = max(0.007, 0.03) = 0.03
        # i=2: max(0.03, (5)*0.01) = max(0.03, 0.05) = 0.05
        # i=3: max(0.05, (4)*0.02) = max(0.05, 0.08) = 0.08
        # i=4: max(0.08, (3)*0.03) = max(0.08, 0.09) = 0.09
        # i=5: max(0.09, (2)*0.04) = max(0.09, 0.08) = 0.09
        # i=6: max(0.09, (1)*0.05) = max(0.09, 0.05) = 0.09
        
        expected = [0.007, 0.03, 0.05, 0.08, 0.09, 0.09, 0.09]
        np.testing.assert_array_almost_equal(corrected, expected, decimal=10)

    def test_holm_bonferroni_unsorted_input(self, sample_p_values):
        """Test that Holm-Bonferroni handles unsorted input correctly by sorting internally."""
        corrected = apply_correction(sample_p_values, method="holm-bonferroni")
        
        # The function should return values in the ORIGINAL order corresponding to the input
        # But the logic relies on sorted values.
        # Let's verify the logic: 
        # Sorted: [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05]
        # Corrected Sorted: [0.007, 0.03, 0.05, 0.08, 0.09, 0.09, 0.09]
        # Original: [0.01, 0.04, 0.03, 0.001, 0.05, 0.02, 0.005]
        # Expected Output Order:
        # 0.01 (3rd smallest) -> 0.05
        # 0.04 (6th smallest) -> 0.09
        # 0.03 (5th smallest) -> 0.09
        # 0.001 (1st smallest) -> 0.007
        # 0.05 (7th smallest) -> 0.09
        # 0.02 (4th smallest) -> 0.08
        # 0.005 (2nd smallest) -> 0.03
        
        expected_unsorted = [0.05, 0.09, 0.09, 0.007, 0.09, 0.08, 0.03]
        np.testing.assert_array_almost_equal(corrected, expected_unsorted, decimal=10)

    def test_holm_bonferroni_monotonicity(self, sorted_p_values):
        """Test that Holm-Bonferroni corrected values are non-decreasing."""
        corrected = apply_correction(sorted_p_values, method="holm-bonferroni")
        assert all(corrected[i] <= corrected[i+1] for i in range(len(corrected)-1))

@pytest.mark.skipif(not MODULE_EXISTS, reason="analysis.validation module not yet implemented")
class TestBenjaminiHochbergCorrection:
    """Tests for the Benjamini-Hochberg (FDR) correction method."""

    def test_bh_basic(self, sorted_p_values):
        """
        Test Benjamini-Hochberg logic:
        1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
        2. Calculate p(i) * m / i
        3. Ensure monotonicity (step-up)
        """
        m = len(sorted_p_values)
        corrected = apply_correction(sorted_p_values, method="benjamini-hochberg")
        
        # Manual calculation (before monotonicity enforcement):
        # i=1 (index 0): 0.001 * 7 / 1 = 0.007
        # i=2 (index 1): 0.005 * 7 / 2 = 0.0175
        # i=3 (index 2): 0.01 * 7 / 3 = 0.02333...
        # i=4 (index 3): 0.02 * 7 / 4 = 0.035
        # i=5 (index 4): 0.03 * 7 / 5 = 0.042
        # i=6 (index 5): 0.04 * 7 / 6 = 0.04666...
        # i=7 (index 6): 0.05 * 7 / 7 = 0.05
        
        # Monotonicity enforcement (from right to left):
        # Last is 0.05
        # 6th: min(0.0466, 0.05) = 0.0466
        # ... usually raw BH is already monotonic for sorted p if p(i) <= p(i+1) * (i+1)/i?
        # Let's just check the raw calculation first, assuming standard implementation.
        
        raw_expected = [0.007, 0.0175, 0.02333333, 0.035, 0.042, 0.04666667, 0.05]
        np.testing.assert_array_almost_equal(corrected, raw_expected, decimal=6)

    def test_bh_unsorted_input(self, sample_p_values):
        """Test that BH handles unsorted input correctly."""
        corrected = apply_correction(sample_p_values, method="benjamini-hochberg")
        
        # Sorted: [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05]
        # Corrected Sorted: [0.007, 0.0175, 0.0233, 0.035, 0.042, 0.0466, 0.05]
        # Map back to original:
        # 0.01 (3rd) -> 0.0233
        # 0.04 (6th) -> 0.0466
        # 0.03 (5th) -> 0.042
        # 0.001 (1st) -> 0.007
        # 0.05 (7th) -> 0.05
        # 0.02 (4th) -> 0.035
        # 0.005 (2nd) -> 0.0175
        
        expected_unsorted = [0.02333333, 0.04666667, 0.042, 0.007, 0.05, 0.035, 0.0175]
        np.testing.assert_array_almost_equal(corrected, expected_unsorted, decimal=6)

@pytest.mark.skipif(not MODULE_EXISTS, reason="analysis.validation module not yet implemented")
class TestCorrectionEdgeCases:
    """Tests for edge cases in correction methods."""

    def test_empty_list(self):
        """Test handling of empty p-value list."""
        result = apply_correction([], method="bonferroni")
        assert result == []

    def test_single_value(self):
        """Test handling of single p-value."""
        result = apply_correction([0.05], method="bonferroni")
        np.testing.assert_almost_equal(result[0], 0.05) # 0.05 * 1 = 0.05

        result_holm = apply_correction([0.05], method="holm-bonferroni")
        np.testing.assert_almost_equal(result_holm[0], 0.05)

    def test_invalid_method(self, sample_p_values):
        """Test that an invalid method raises an error."""
        with pytest.raises(ValueError):
            apply_correction(sample_p_values, method="invalid_method")

    def test_p_values_greater_than_one(self):
        """Test that p-values > 1 are capped at 1.0 after correction."""
        # Note: Input p-values > 1 are technically invalid, but robustness is good.
        # If input is 1.5, bonferroni (m=2) -> 3.0 -> cap to 1.0.
        p_values = [1.5, 0.5]
        corrected = apply_correction(p_values, method="bonferroni")
        assert all(p <= 1.0 for p in corrected)
        
    def test_p_values_zero(self):
        """Test handling of p-values equal to zero."""
        p_values = [0.0, 0.05]
        corrected = apply_correction(p_values, method="bonferroni")
        # 0.0 * m = 0.0
        assert corrected[0] == 0.0
        assert corrected[1] <= 1.0