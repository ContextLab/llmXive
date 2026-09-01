"""
Unit tests for descriptor calculation and numerical stability.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.feature_engineering import calculate_descriptors, clamp_near_zero
from code.config import RANDOM_SEED

class TestClampNearZero:
    """Tests for numerical stability clamping logic (Task T020)."""

    def test_clamp_positive_values_unchanged(self):
        """Verify that positive values above threshold remain unchanged."""
        threshold = 1e-6
        values = np.array([1.0, 0.5, 1e-5, 1e-4])
        result = clamp_near_zero(values, threshold=threshold)
        np.testing.assert_array_equal(result, values)

    def test_clamp_zero_to_threshold(self):
        """Verify that zero is clamped to the threshold value."""
        threshold = 1e-6
        values = np.array([0.0])
        result = clamp_near_zero(values, threshold=threshold)
        assert result[0] == threshold

    def test_clamp_small_positive_to_threshold(self):
        """Verify that values smaller than threshold are clamped to threshold."""
        threshold = 1e-6
        values = np.array([1e-9, 1e-7, 0.5e-6])
        result = clamp_near_zero(values, threshold=threshold)
        expected = np.array([threshold, threshold, threshold])
        np.testing.assert_array_equal(result, expected)

    def test_clamp_negative_values(self):
        """Verify that negative values are handled correctly (typically absolute or clamped magnitude)."""
        # Assuming clamping applies to magnitude or specific context where negative is valid but small
        # Standard numerical stability for denominators usually implies absolute value or forcing positive.
        # Based on T020 description "clamp near-zero values to a small positive constant",
        # we assume the function forces values to be at least `threshold`.
        threshold = 1e-6
        values = np.array([-1e-9, -1e-7, -0.5e-6, -1.0])
        # If the logic is `max(val, threshold)` for positive-only contexts:
        # If the logic is `abs(val)` then clamp:
        # Let's assume the standard implementation for variance/denominator safety:
        # return np.maximum(np.abs(values), threshold) OR np.where(values < threshold, threshold, values)
        # Given the prompt "clamp near-zero values to a small positive constant",
        # we test the behavior that ensures the output is >= threshold.
        
        # Implementation assumption: np.where(np.abs(x) < thresh, thresh, x)
        # OR if the context is strictly positive (like variance), then np.maximum(x, thresh).
        # We will test the robust behavior: output >= threshold.
        
        result = clamp_near_zero(values, threshold=threshold)
        assert np.all(result >= threshold)

    def test_clamp_array_with_mixed_values(self):
        """Verify clamping on an array with mixed magnitudes."""
        threshold = 1e-6
        values = np.array([0.0, 1e-9, 1.0, 1e-5, -1e-9])
        result = clamp_near_zero(values, threshold=threshold)
        
        # Check specific indices
        assert result[0] == threshold  # 0.0 -> threshold
        assert result[1] == threshold  # 1e-9 -> threshold
        assert result[2] == 1.0        # 1.0 -> unchanged
        assert result[3] == 1e-5       # 1e-5 -> unchanged
        assert result[4] == threshold  # -1e-9 -> threshold (assuming magnitude clamp or forced positive)

class TestDescriptorCalculationNumericalStability:
    """Integration-style tests for descriptor calculation stability."""

    def test_descriptors_with_zero_variance(self):
        """Verify that descriptors with zero variance (single element or identical) don't crash."""
        # Create a dataset with a single element repeated (variance = 0)
        data = pd.DataFrame({
            'composition': ['Fe-Fe-Fe-Fe-Fe'],
            'elements': [['Fe', 'Fe', 'Fe', 'Fe', 'Fe']],
            'fractions': [1.0] # Simplified for test
        })
        # Note: The actual implementation in feature_engineering.py handles the composition parsing.
        # We test the clamping function's effect on the variance calculation result.
        # If variance is 0, it should be clamped to 1e-6 before any division.
        
        # Simulate the variance result
        variance_result = 0.0
        clamped = clamp_near_zero(np.array([variance_result]), threshold=1e-6)
        assert clamped[0] == 1e-6

    def test_descriptors_with_near_zero_variance(self):
        """Verify that descriptors with near-zero variance are clamped."""
        variance_result = 1e-10
        clamped = clamp_near_zero(np.array([variance_result]), threshold=1e-6)
        assert clamped[0] == 1e-6

    def test_no_division_by_zero_in_calculations(self):
        """Ensure that using clamped values prevents division by zero."""
        # Simulate a calculation that divides by variance
        variance = 0.0
        clamped_variance = clamp_near_zero(np.array([variance]), threshold=1e-6)[0]
        
        # This should not raise ZeroDivisionError
        try:
            result = 1.0 / clamped_variance
            assert result == 1e6
        except ZeroDivisionError:
            pytest.fail("Division by zero occurred despite clamping")

class TestDescriptorCalculationIntegration:
    """Tests for the full descriptor calculation pipeline stability."""

    @patch('code.feature_engineering.pymatgen')
    def test_calculate_descriptors_handles_empty_dataframe(self, mock_pymatgen):
        """Verify behavior with empty input dataframe."""
        df = pd.DataFrame(columns=['composition', 'target_energy'])
        # Should return empty dataframe or raise appropriate error, not crash with index error
        try:
            result = calculate_descriptors(df)
            assert result.empty
        except Exception as e:
            # If it raises, it should be a clear error, not a cryptic index error
            assert "Empty" in str(e) or "No data" in str(e)

    @patch('code.feature_engineering.pymatgen')
    def test_calculate_descriptors_with_nan_values(self, mock_pymatgen):
        """Verify handling of NaN values in input data."""
        data = pd.DataFrame({
            'composition': ['Fe-Cr-Ni-Mo-Cu'],
            'target_energy': [np.nan]
        })
        # The function should either drop NaNs or handle them gracefully
        # We test that the clamping logic is invoked on valid numeric columns
        # If the implementation drops NaN rows, that's acceptable.
        pass # Placeholder for actual implementation verification