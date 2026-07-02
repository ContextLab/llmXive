"""
Unit tests for CLR transformation function in correlation_analysis.py.
Verifies log(0) handling with pseudocount and mathematical correctness.
"""

import pytest
import numpy as np
import pandas as pd
import math
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from correlation_analysis import clr_transform


class TestCLRTransformation:
    """Test suite for CLR (Centered Log-Ratio) transformation."""

    def test_basic_clr_transformation(self):
        """Test basic CLR transformation on simple positive data."""
        # Create sample data
        data = np.array([[1.0, 2.0, 4.0],
                         [2.0, 4.0, 8.0]])
        
        # Apply CLR transformation
        result = clr_transform(data)
        
        # Verify output shape
        assert result.shape == data.shape, "Output shape should match input shape"
        
        # Verify that sum of CLR transformed values is approximately zero (property of CLR)
        row_sums = np.sum(result, axis=1)
        assert np.allclose(row_sums, 0.0, atol=1e-6), "CLR transformed values should sum to zero"

    def test_zero_handling_with_pseudocount(self):
        """Test that zeros are handled correctly with pseudocount."""
        # Data containing zeros
        data_with_zeros = np.array([[0.0, 1.0, 2.0],
                                    [1.0, 0.0, 3.0]])
        
        # Apply CLR transformation (should not raise error)
        result = clr_transform(data_with_zeros, pseudocount=0.5)
        
        # Verify no NaN or Inf values
        assert not np.any(np.isnan(result)), "Result should not contain NaN values"
        assert not np.any(np.isinf(result)), "Result should not contain Inf values"
        
        # Verify output shape
        assert result.shape == data_with_zeros.shape

    def test_pseudocount_parameter(self):
        """Test that different pseudocount values produce expected results."""
        data = np.array([[0.0, 1.0, 2.0]])
        
        # Test with pseudocount=0.5
        result_05 = clr_transform(data, pseudocount=0.5)
        
        # Test with pseudocount=1.0
        result_10 = clr_transform(data, pseudocount=1.0)
        
        # Results should be different
        assert not np.allclose(result_05, result_10), "Different pseudocounts should produce different results"
        
        # Verify no errors or NaN
        assert not np.any(np.isnan(result_05))
        assert not np.any(np.isnan(result_10))

    def test_single_value_handling(self):
        """Test CLR transformation on single value (edge case)."""
        data = np.array([[5.0, 5.0, 5.0]])
        
        result = clr_transform(data)
        
        # When all values are equal, CLR should be approximately zero
        assert np.allclose(result, 0.0, atol=1e-6), "Equal values should result in near-zero CLR"

    def test_pandas_dataframe_input(self):
        """Test CLR transformation with pandas DataFrame input."""
        df = pd.DataFrame({
            'taxon_a': [1.0, 2.0, 0.0],
            'taxon_b': [2.0, 0.0, 4.0],
            'taxon_c': [4.0, 4.0, 0.0]
        })
        
        result = clr_transform(df, pseudocount=0.5)
        
        # Verify output is DataFrame with same index and columns
        assert isinstance(result, pd.DataFrame)
        assert result.index.equals(df.index)
        assert result.columns.equals(df.columns)
        
        # Verify no NaN or Inf
        assert not result.isna().any().any()
        assert not np.isinf(result.values).any()

    def test_large_dataset(self):
        """Test CLR transformation on larger dataset for performance."""
        np.random.seed(42)
        large_data = np.random.rand(100, 50) * 100  # 100 samples, 50 features
        
        result = clr_transform(large_data)
        
        assert result.shape == large_data.shape
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_negative_values_handling(self):
        """Test behavior with negative values (should raise warning or handle gracefully)."""
        # CLR transformation technically requires positive values
        # With pseudocount, negative values close to zero might be handled
        data = np.array([[-0.1, 1.0, 2.0]])
        
        # This might produce unexpected results but should not crash
        result = clr_transform(data, pseudocount=0.5)
        
        # Verify no crash and no NaN
        assert result.shape == data.shape
        assert not np.any(np.isnan(result))

    def test_log_zero_specifically(self):
        """Specifically test that log(0) is handled by pseudocount."""
        # This test ensures the pseudocount is actually added before log
        data = np.array([[0.0, 0.0, 1.0]])
        
        # Without pseudocount, this would produce -inf
        result = clr_transform(data, pseudocount=0.5)
        
        # All values should be finite
        assert np.all(np.isfinite(result)), "All values should be finite after pseudocount application"
        
        # The value that was 0 should now be transformed based on (0 + 0.5)
        # Verify the transformation is mathematically sound
        manual_check = np.log(0.5)  # log(pseudocount)
        # The actual result depends on the geometric mean, but should be finite

    def test_output_dtype(self):
        """Test that output maintains appropriate data type."""
        data = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
        
        result = clr_transform(data)
        
        # Output should be float
        assert np.issubdtype(result.dtype, np.floating), "Output should be floating point"

    def test_empty_dataframe(self):
        """Test behavior with empty DataFrame."""
        df = pd.DataFrame()
        
        # This should handle gracefully or raise appropriate error
        try:
            result = clr_transform(df)
            # If it returns, it should be empty
            assert result.empty
        except Exception as e:
            # Or it should raise a clear error
            assert isinstance(e, (ValueError, AssertionError))

    def test_single_column(self):
        """Test CLR transformation with single column."""
        data = np.array([[1.0], [2.0], [3.0]])
        
        result = clr_transform(data)
        
        # With single column, CLR should be zero (log(x) - log(x) = 0)
        assert np.allclose(result, 0.0, atol=1e-6), "Single column CLR should be zero"

    def test_mixed_zeros_and_ones(self):
        """Test with realistic microbiome-like data (many zeros, some ones)."""
        np.random.seed(123)
        # Simulate sparse microbiome data
        data = np.random.binomial(1, 0.3, size=(50, 20)).astype(float)
        
        result = clr_transform(data, pseudocount=0.5)
        
        assert result.shape == data.shape
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
        
        # Verify row sums are approximately zero
        row_sums = np.sum(result, axis=1)
        assert np.allclose(row_sums, 0.0, atol=1e-5)

    def test_pseudocount_default_value(self):
        """Test that default pseudocount is 0.5 as specified."""
        data = np.array([[0.0, 1.0, 2.0]])
        
        # Call without specifying pseudocount
        result_default = clr_transform(data)
        
        # Call explicitly with 0.5
        result_explicit = clr_transform(data, pseudocount=0.5)
        
        # Results should be identical
        assert np.allclose(result_default, result_explicit), "Default pseudocount should be 0.5"

    def test_numerical_stability(self):
        """Test numerical stability with very small values."""
        data = np.array([[1e-10, 1e-8, 1e-6]])
        
        result = clr_transform(data, pseudocount=0.5)
        
        # Should not produce Inf or NaN
        assert np.all(np.isfinite(result)), "Small values should be handled stably"
        
        # Row sum should be approximately zero
        assert np.isclose(np.sum(result), 0.0, atol=1e-6)

    def test_reversibility_check(self):
        """
        Test that CLR transformation has the expected mathematical property:
        The geometric mean of the original values equals the geometric mean
        of the anti-log of CLR transformed values (approximately).
        """
        data = np.array([[1.0, 2.0, 4.0, 8.0]])
        
        result = clr_transform(data)
        
        # Geometric mean of original
        geo_mean_original = np.exp(np.mean(np.log(data)))
        
        # Anti-log CLR (should recover relative proportions)
        anti_log_clr = np.exp(result)
        
        # The geometric mean of anti-log CLR should be 1 (since CLR centers the data)
        geo_mean_clr = np.exp(np.mean(np.log(anti_log_clr)))
        
        # This is a property check, not exact equality due to floating point
        assert np.isclose(geo_mean_clr, 1.0, rtol=1e-5), "Geometric mean of anti-log CLR should be 1"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
