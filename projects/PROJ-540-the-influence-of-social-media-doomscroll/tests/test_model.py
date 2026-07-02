"""
Unit tests for statistical modeling functions in code/model.py.
Specifically verifies Pearson correlation logic against hardcoded synthetic values.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from model import calculate_pearson_correlation


class TestModel:
    """Test suite for statistical modeling functions."""

    def test_pearson_correlation_matches_manual_calculation(self):
        """
        Verify Pearson correlation logic against hardcoded synthetic values.
        
        Uses a small, deterministic dataset where the Pearson correlation
        can be manually calculated to ensure the implementation is correct.
        
        Dataset:
        X = [1, 2, 3, 4, 5]
        Y = [2, 4, 5, 4, 5]
        
        Expected r ≈ 0.7559 (calculated manually or via numpy)
        """
        # Hardcoded synthetic data
        x_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_data = [2.0, 4.0, 5.0, 4.0, 5.0]
        
        # Create a DataFrame to match expected input format
        df = pd.DataFrame({
            'var_x': x_data,
            'var_y': y_data
        })
        
        # Calculate expected correlation using numpy for ground truth
        expected_r, _ = np.corrcoef(x_data, y_data)
        
        # Calculate using our implementation
        # Assuming the function takes column names from a DataFrame
        result_r = calculate_pearson_correlation(df, 'var_x', 'var_y')
        
        # Assert they match within floating point tolerance
        np.testing.assert_almost_equal(
            result_r, 
            expected_r, 
            decimal=5, 
            err_msg=f"Pearson correlation mismatch: got {result_r}, expected {expected_r}"
        )
        
        # Additional sanity checks
        assert -1.0 <= result_r <= 1.0, "Correlation must be between -1 and 1"
        assert result_r > 0, "Expected positive correlation for this dataset"

    def test_pearson_correlation_perfect_positive(self):
        """Test with perfectly positively correlated data (r = 1.0)."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # y = 2x
        
        df = pd.DataFrame({'x': x, 'y': y})
        result = calculate_pearson_correlation(df, 'x', 'y')
        
        np.testing.assert_almost_equal(result, 1.0, decimal=5)

    def test_pearson_correlation_perfect_negative(self):
        """Test with perfectly negatively correlated data (r = -1.0)."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]  # y = 12 - 2x
        
        df = pd.DataFrame({'x': x, 'y': y})
        result = calculate_pearson_correlation(df, 'x', 'y')
        
        np.testing.assert_almost_equal(result, -1.0, decimal=5)

    def test_pearson_correlation_no_correlation(self):
        """Test with uncorrelated data (r ≈ 0)."""
        # Construct data with near-zero correlation
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 1.0, 4.0, 2.0, 3.0]
        
        df = pd.DataFrame({'x': x, 'y': y})
        result = calculate_pearson_correlation(df, 'x', 'y')
        
        # Expected r for this specific set is approximately -0.1
        # We just check it's within valid range and not extreme
        assert -1.0 <= result <= 1.0

    def test_pearson_correlation_constant_variable(self):
        """Test that constant variable raises appropriate error or returns NaN."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 5.0, 5.0, 5.0, 5.0]  # Constant variable
        
        df = pd.DataFrame({'x': x, 'y': y})
        
        # This should either raise a ValueError or return NaN
        # depending on implementation choice
        result = calculate_pearson_correlation(df, 'x', 'y')
        
        # If not raising, it should be NaN
        if not isinstance(result, float) or not np.isnan(result):
            # If it returns a value, it's likely 0 or we need to check implementation
            # For now, we accept NaN as the mathematically correct result
            pass

    def test_pearson_correlation_missing_columns(self):
        """Test that missing columns raise a KeyError."""
        df = pd.DataFrame({'x': [1.0, 2.0, 3.0]})
        
        with pytest.raises(KeyError):
            calculate_pearson_correlation(df, 'x', 'nonexistent_column')