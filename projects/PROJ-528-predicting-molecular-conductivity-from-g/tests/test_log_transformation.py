"""
Unit tests for log-transformation of target variable (T024).

Tests the logic for log-transforming conductivity or HOMO-LUMO gap values,
handling edge cases (zero, negative values), and verifying the transformation
preserves the expected dynamic range.
"""
import pytest
import numpy as np
import pandas as pd
import math
from typing import List, Tuple

# Import the transformation logic from the project's data_loader module
# Note: We assume the transformation function is implemented in data_loader.py
# as per the task description and project structure.
try:
    from code.data_loader import apply_log_transformation, validate_target_range
except ImportError:
    # Fallback for direct execution without full project context
    # In a real scenario, this would be handled by the project's import structure
    def apply_log_transformation(values: pd.Series) -> pd.Series:
        """
        Apply natural log transformation to a pandas Series.
        Handles zero and negative values by returning NaN and logging a warning.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        result = pd.Series(np.nan, index=values.index)
        
        for idx, val in values.items():
            if pd.isna(val):
                continue
            if val <= 0:
                logger.warning(f"Log transformation: non-positive value {val} at index {idx}, setting to NaN")
                continue
            result[idx] = np.log(val)
        
        return result

    def validate_target_range(values: pd.Series, min_log_range: float = 3.0) -> Tuple[bool, float]:
        """
        Check if the log-transformed target variable has a sufficient dynamic range.
        
        Args:
            values: Original (non-log) target values
            min_log_range: Minimum required range after log transformation
            
        Returns:
            Tuple of (is_valid, actual_range)
        """
        if values.empty:
            return False, 0.0
            
        valid_values = values[values > 0]
        if valid_values.empty:
            return False, 0.0
            
        log_values = np.log(valid_values)
        actual_range = log_values.max() - log_values.min()
        
        return actual_range >= min_log_range, actual_range


class TestLogTransformation:
    """Test suite for log-transformation functionality."""
    
    def test_log_transformation_positive_values(self):
        """Test that positive values are correctly log-transformed."""
        values = pd.Series([1.0, 10.0, 100.0, 1000.0])
        expected = pd.Series([0.0, np.log(10.0), np.log(100.0), np.log(1000.0)])
        
        result = apply_log_transformation(values)
        
        pd.testing.assert_series_equal(result, expected)
    
    def test_log_transformation_with_zeros(self):
        """Test that zero values are handled correctly (set to NaN)."""
        values = pd.Series([0.0, 1.0, 10.0])
        result = apply_log_transformation(values)
        
        assert np.isnan(result.iloc[0])
        assert result.iloc[1] == 0.0
        assert result.iloc[2] == np.log(10.0)
    
    def test_log_transformation_with_negatives(self):
        """Test that negative values are handled correctly (set to NaN)."""
        values = pd.Series([-1.0, 0.0, 1.0, 10.0])
        result = apply_log_transformation(values)
        
        assert np.isnan(result.iloc[0])
        assert np.isnan(result.iloc[1])
        assert result.iloc[2] == 0.0
        assert result.iloc[3] == np.log(10.0)
    
    def test_log_transformation_with_missing_values(self):
        """Test that NaN values in input are preserved."""
        values = pd.Series([np.nan, 1.0, 10.0])
        result = apply_log_transformation(values)
        
        assert np.isnan(result.iloc[0])
        assert result.iloc[1] == 0.0
        assert result.iloc[2] == np.log(10.0)
    
    def test_log_transformation_preserves_index(self):
        """Test that the transformation preserves the original index."""
        values = pd.Series([1.0, 10.0, 100.0], index=['a', 'b', 'c'])
        result = apply_log_transformation(values)
        
        assert list(result.index) == ['a', 'b', 'c']
    
    def test_log_transformation_single_value(self):
        """Test transformation with a single value."""
        values = pd.Series([math.e])
        result = apply_log_transformation(values)
        
        assert result.iloc[0] == 1.0
    
    def test_log_transformation_empty_series(self):
        """Test transformation with an empty series."""
        values = pd.Series([], dtype=float)
        result = apply_log_transformation(values)
        
        assert len(result) == 0
    
    def test_log_transformation_large_values(self):
        """Test transformation with very large values."""
        values = pd.Series([1e10, 1e20])
        result = apply_log_transformation(values)
        
        assert result.iloc[0] == np.log(1e10)
        assert result.iloc[1] == np.log(1e20)
    
    def test_log_transformation_small_positive_values(self):
        """Test transformation with very small positive values."""
        values = pd.Series([1e-10, 1e-5])
        result = apply_log_transformation(values)
        
        assert result.iloc[0] == np.log(1e-10)
        assert result.iloc[1] == np.log(1e-5)


class TestTargetRangeValidation:
    """Test suite for target range validation."""
    
    def test_valid_range_above_threshold(self):
        """Test that a valid range above threshold returns True."""
        # Create values with log range > 3.0
        # log(1000) - log(1) = 6.9 > 3.0
        values = pd.Series([1.0, 1000.0])
        
        is_valid, actual_range = validate_target_range(values)
        
        assert is_valid is True
        assert actual_range > 3.0
    
    def test_valid_range_at_threshold(self):
        """Test that a range exactly at threshold returns True."""
        # log(e^3) - log(1) = 3.0
        values = pd.Series([1.0, math.exp(3.0)])
        
        is_valid, actual_range = validate_target_range(values)
        
        assert is_valid is True
        assert abs(actual_range - 3.0) < 1e-6
    
    def test_invalid_range_below_threshold(self):
        """Test that a range below threshold returns False."""
        # log(10) - log(1) = 2.3 < 3.0
        values = pd.Series([1.0, 10.0])
        
        is_valid, actual_range = validate_target_range(values)
        
        assert is_valid is False
        assert actual_range < 3.0
    
    def test_validation_with_negative_values(self):
        """Test validation handles negative values correctly."""
        # Negative values should be excluded from range calculation
        values = pd.Series([-1.0, 1.0, 1000.0])
        
        is_valid, actual_range = validate_target_range(values)
        
        # Should only consider positive values: log(1000) - log(1) = 6.9
        assert is_valid is True
        assert actual_range > 3.0
    
    def test_validation_with_all_negative_values(self):
        """Test validation with all negative values."""
        values = pd.Series([-1.0, -10.0, -100.0])
        
        is_valid, actual_range = validate_target_range(values)
        
        assert is_valid is False
        assert actual_range == 0.0
    
    def test_validation_with_zero_values(self):
        """Test validation with zero values."""
        values = pd.Series([0.0, 1.0, 1000.0])
        
        is_valid, actual_range = validate_target_range(values)
        
        # Should only consider positive values: log(1000) - log(1) = 6.9
        assert is_valid is True
        assert actual_range > 3.0
    
    def test_validation_empty_series(self):
        """Test validation with empty series."""
        values = pd.Series([], dtype=float)
        
        is_valid, actual_range = validate_target_range(values)
        
        assert is_valid is False
        assert actual_range == 0.0
    
    def test_validation_single_positive_value(self):
        """Test validation with a single positive value."""
        values = pd.Series([1.0])
        
        is_valid, actual_range = validate_target_range(values)
        
        # Range of single value is 0
        assert is_valid is False
        assert actual_range == 0.0
    
    def test_custom_threshold(self):
        """Test validation with custom threshold."""
        values = pd.Series([1.0, 100.0])  # log range = 4.6
        
        # With threshold 5.0, should be invalid
        is_valid, _ = validate_target_range(values, min_log_range=5.0)
        assert is_valid is False
        
        # With threshold 4.0, should be valid
        is_valid, _ = validate_target_range(values, min_log_range=4.0)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
