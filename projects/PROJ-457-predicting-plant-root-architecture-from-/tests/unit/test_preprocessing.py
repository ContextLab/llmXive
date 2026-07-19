"""
Unit tests for preprocessing functions, specifically focusing on log-transformation
handling of zeros and negative values as required by User Story 1.
"""

import math
import pytest
import pandas as pd
import numpy as np
from preprocessing import apply_log_transformation


class TestLogTransformation:
    """Test suite for apply_log_transformation function."""

    def test_normal_positive_values(self):
        """Test that normal positive values are transformed correctly."""
        df = pd.DataFrame({
            'root_length': [1.0, 10.0, 100.0],
            'branching_density': [2.0, 20.0, 200.0]
        })
        
        result = apply_log_transformation(df, ['root_length', 'branching_density'])
        
        # Check that log(1) = 0
        assert math.isclose(result['root_length'].iloc[0], 0.0, rel_tol=1e-9)
        # Check that log(10) ~ 2.302
        assert math.isclose(result['root_length'].iloc[1], math.log(10.0), rel_tol=1e-9)
        # Check that log(100) ~ 4.605
        assert math.isclose(result['root_length'].iloc[2], math.log(100.0), rel_tol=1e-9)

    def test_zero_values_handling(self):
        """Test that zero values are handled by adding a small epsilon."""
        df = pd.DataFrame({
            'root_length': [0.0, 1.0, 10.0],
            'other_col': [1.0, 2.0, 3.0]
        })
        
        result = apply_log_transformation(df, ['root_length'])
        
        # The zero value should be transformed to log(epsilon)
        # Default epsilon is usually 1e-8 or similar
        # We verify it's a valid number and not -inf or NaN
        transformed_zero = result['root_length'].iloc[0]
        assert not math.isnan(transformed_zero)
        assert not math.isinf(transformed_zero)
        assert transformed_zero < 0  # log of a small number < 1 is negative
        
        # Verify other values are still correct
        assert math.isclose(result['root_length'].iloc[1], 0.0, rel_tol=1e-9)

    def test_negative_values_handling(self):
        """Test that negative values raise an appropriate error or are handled."""
        df = pd.DataFrame({
            'root_length': [-5.0, 1.0, 10.0],
            'other_col': [1.0, 2.0, 3.0]
        })
        
        # According to the task, we should handle negatives.
        # The implementation should either:
        # 1. Raise an error for negative values
        # 2. Apply a transformation that handles them (e.g., log(x + shift))
        # Based on typical scientific preprocessing, we expect an error or warning
        # for negative biological measurements.
        
        # For this test, we verify that the function handles the case gracefully
        # (either by raising a clear error or by transforming appropriately)
        with pytest.raises((ValueError, RuntimeError)):
            apply_log_transformation(df, ['root_length'])

    def test_mixed_zeros_and_positives(self):
        """Test a mix of zero and positive values."""
        df = pd.DataFrame({
            'surface_area': [0.0, 0.0, 1.0, 10.0, 100.0]
        })
        
        result = apply_log_transformation(df, ['surface_area'])
        
        # All values should be finite numbers
        for val in result['surface_area']:
            assert not math.isnan(val)
            assert not math.isinf(val)
        
        # Verify the non-zero values are correct
        assert math.isclose(result['surface_area'].iloc[2], 0.0, rel_tol=1e-9)
        assert math.isclose(result['surface_area'].iloc[3], math.log(10.0), rel_tol=1e-9)

    def test_empty_dataframe(self):
        """Test behavior with an empty dataframe."""
        df = pd.DataFrame({'root_length': []})
        
        result = apply_log_transformation(df, ['root_length'])
        
        assert result.empty

    def test_nonexistent_column(self):
        """Test that a clear error is raised for nonexistent columns."""
        df = pd.DataFrame({
            'root_length': [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(KeyError):
            apply_log_transformation(df, ['nonexistent_column'])

    def test_multiple_columns_with_zeros(self):
        """Test transformation on multiple columns containing zeros."""
        df = pd.DataFrame({
            'root_length': [0.0, 1.0, 10.0],
            'branching_density': [0.0, 0.0, 1.0],
            'surface_area': [1.0, 2.0, 3.0]
        })
        
        result = apply_log_transformation(df, ['root_length', 'branching_density', 'surface_area'])
        
        # Verify all transformed columns exist and have valid values
        for col in ['root_length', 'branching_density', 'surface_area']:
            assert col in result.columns
            for val in result[col]:
                assert not math.isnan(val)
                assert not math.isinf(val)

    def test_preserves_dataframe_structure(self):
        """Test that the output dataframe has the same shape and index."""
        df = pd.DataFrame({
            'root_length': [1.0, 2.0, 3.0],
            'other_col': ['a', 'b', 'c']
        }, index=['row1', 'row2', 'row3'])
        
        result = apply_log_transformation(df, ['root_length'])
        
        assert result.shape == df.shape
        assert list(result.index) == list(df.index)
        assert list(result.columns) == list(df.columns)

    def test_epsilon_parameter(self):
        """Test that custom epsilon parameter works correctly."""
        df = pd.DataFrame({
            'root_length': [0.0, 1.0, 10.0]
        })
        
        # Test with a larger epsilon
        result = apply_log_transformation(df, ['root_length'], epsilon=1e-4)
        
        # log(1e-4) = -9.210...
        expected_log_epsilon = math.log(1e-4)
        assert math.isclose(result['root_length'].iloc[0], expected_log_epsilon, rel_tol=1e-9)
        
        # Test with a smaller epsilon
        result_small = apply_log_transformation(df, ['root_length'], epsilon=1e-10)
        expected_log_epsilon_small = math.log(1e-10)
        assert math.isclose(result_small['root_length'].iloc[0], expected_log_epsilon_small, rel_tol=1e-9)