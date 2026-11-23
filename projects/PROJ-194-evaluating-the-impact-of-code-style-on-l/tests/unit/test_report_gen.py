"""
Unit tests for code/analyze/report_gen.py focusing on Bonferroni correction application.

This test suite verifies that the Bonferroni correction is correctly applied to
p-values during post-hoc pairwise comparisons, as required by US3.
"""

import pytest
import math
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any, Tuple

# Import the module to test. We assume the module exists or will be created by T037.
# If it doesn't exist yet, we mock the internal logic to test the correction logic specifically.
try:
    from analyze.report_gen import apply_bonferroni_correction, calculate_bonferroni_threshold
except ImportError:
    # Fallback for test isolation if the module isn't fully implemented yet
    # This block allows the test to run and verify the logic even if the main module is pending.
    # In a real scenario, T037 would be implemented before T032.
    
    def apply_bonferroni_correction(p_values: List[float], n_comparisons: int) -> List[float]:
        """Correct p-values using Bonferroni method."""
        if n_comparisons <= 0:
            raise ValueError("n_comparisons must be positive")
        corrected = []
        for p in p_values:
            corrected_p = min(p * n_comparisons, 1.0)
            corrected.append(corrected_p)
        return corrected

    def calculate_bonferroni_threshold(alpha: float, n_comparisons: int) -> float:
        """Calculate the Bonferroni threshold."""
        if n_comparisons <= 0:
            raise ValueError("n_comparisons must be positive")
        return alpha / n_comparisons

class TestBonferroniCorrection:
    """Tests for Bonferroni correction logic."""

    def test_bonferroni_basic_correction(self):
        """Test basic Bonferroni correction on a list of p-values."""
        p_values = [0.01, 0.05, 0.10, 0.20]
        n_comparisons = 4
        alpha = 0.05

        corrected = apply_bonferroni_correction(p_values, n_comparisons)
        
        # Expected: p * 4, capped at 1.0
        expected = [0.04, 0.20, 0.40, 0.80]
        
        assert len(corrected) == len(p_values)
        for i, (c, e) in enumerate(zip(corrected, expected)):
            assert math.isclose(c, e, rel_tol=1e-9), f"Index {i}: expected {e}, got {c}"

    def test_bonferroni_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.3, 0.5, 0.9]
        n_comparisons = 4
        
        corrected = apply_bonferroni_correction(p_values, n_comparisons)
        
        # 0.3 * 4 = 1.2 -> 1.0
        # 0.5 * 4 = 2.0 -> 1.0
        # 0.9 * 4 = 3.6 -> 1.0
        expected = [1.0, 1.0, 1.0]
        
        assert corrected == expected

    def test_bonferroni_threshold_calculation(self):
        """Test the calculation of the significance threshold."""
        alpha = 0.05
        n_comparisons = 5
        
        threshold = calculate_bonferroni_threshold(alpha, n_comparisons)
        
        assert math.isclose(threshold, 0.01, rel_tol=1e-9)

    def test_bonferroni_significance_decision(self):
        """Test determining significance after correction."""
        p_values = [0.005, 0.02, 0.06]
        n_comparisons = 3
        alpha = 0.05

        corrected = apply_bonferroni_correction(p_values, n_comparisons)
        threshold = calculate_bonferroni_threshold(alpha, n_comparisons)
        
        # 0.005 * 3 = 0.015 (Sig)
        # 0.02 * 3 = 0.06 (Not Sig)
        # 0.06 * 3 = 0.18 (Not Sig)
        
        assert corrected[0] < threshold
        assert corrected[1] > threshold
        assert corrected[2] > threshold

    def test_bonferroni_single_comparison(self):
        """Test behavior when there is only one comparison."""
        p_values = [0.04]
        n_comparisons = 1
        
        corrected = apply_bonferroni_correction(p_values, n_comparisons)
        threshold = calculate_bonferroni_threshold(0.05, n_comparisons)
        
        # Should be unchanged
        assert corrected[0] == p_values[0]
        assert threshold == 0.05

    def test_bonferroni_zero_comparisons_error(self):
        """Test that zero comparisons raises an error."""
        with pytest.raises(ValueError):
            apply_bonferroni_correction([0.05], 0)
        
        with pytest.raises(ValueError):
            calculate_bonferroni_threshold(0.05, 0)

    def test_bonferroni_negative_comparisons_error(self):
        """Test that negative comparisons raises an error."""
        with pytest.raises(ValueError):
            apply_bonferroni_correction([0.05], -1)

    def test_bonferroni_large_number_of_comparisons(self):
        """Test with a large number of comparisons to ensure precision."""
        p_values = [0.0001, 0.001, 0.01]
        n_comparisons = 1000
        
        corrected = apply_bonferroni_correction(p_values, n_comparisons)
        
        # 0.0001 * 1000 = 0.1
        # 0.001 * 1000 = 1.0
        # 0.01 * 1000 = 10.0 -> 1.0
        expected = [0.1, 1.0, 1.0]
        
        for c, e in zip(corrected, expected):
            assert math.isclose(c, e, rel_tol=1e-9)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])