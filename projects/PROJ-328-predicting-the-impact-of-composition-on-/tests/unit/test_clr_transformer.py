"""
Unit tests for the CLRTransformer.
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add code to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features.transformer import CLRTransformer

class TestCLRTransformer:
    """Tests for the CLRTransformer class."""

    def test_init(self):
        """Test initialization with default and custom pseudo_count."""
        transformer = CLRTransformer()
        assert transformer.pseudo_count == 1e-6

        transformer_custom = CLRTransformer(pseudo_count=1e-4)
        assert transformer_custom.pseudo_count == 1e-4

    def test_transform_basic(self):
        """Test basic transformation on simple data."""
        transformer = CLRTransformer()
        # Simple ternary composition
        X = np.array([[0.5, 0.3, 0.2]])
        
        result = transformer.transform(X)
        
        assert result.shape == X.shape
        # CLR transformed rows should sum to ~0
        row_sum = result.sum(axis=1)[0]
        assert np.isclose(row_sum, 0, atol=1e-6)

    def test_transform_multiple_rows(self):
        """Test transformation on multiple samples."""
        transformer = CLRTransformer()
        X = np.array([
            [0.9, 0.05, 0.05],
            [0.1, 0.8, 0.1],
            [0.33, 0.33, 0.34]
        ])
        
        result = transformer.transform(X)
        
        assert result.shape == X.shape
        
        # Check each row sums to ~0
        for i in range(X.shape[0]):
            row_sum = result[i].sum()
            assert np.isclose(row_sum, 0, atol=1e-6), f"Row {i} sum is {row_sum}"

    def test_transform_zeros_handling(self):
        """Test that zeros are handled via pseudo_count."""
        transformer = CLRTransformer(pseudo_count=1e-6)
        # Data with a zero (which should be clipped)
        X = np.array([[1.0, 0.0, 0.0]])
        
        # Should not raise an error
        result = transformer.transform(X)
        assert result.shape == X.shape
        assert not np.isnan(result).any()
        assert not np.isinf(result).any()

    def test_fit_is_noop(self):
        """Test that fit() returns self and doesn't change state."""
        transformer = CLRTransformer()
        X = np.array([[0.5, 0.5]])
        
        fitted = transformer.fit(X)
        assert fitted is transformer

    def test_fit_transform(self):
        """Test fit_transform method."""
        transformer = CLRTransformer()
        X = np.array([[0.6, 0.2, 0.2]])
        
        result = transformer.fit_transform(X)
        
        assert result.shape == X.shape
        assert np.isclose(result.sum(), 0, atol=1e-6)

    def test_invalid_input_empty(self):
        """Test that empty input raises ValueError."""
        transformer = CLRTransformer()
        X = np.array([]).reshape(0, 3)
        
        with pytest.raises(ValueError):
            transformer.transform(X)

    def test_invalid_input_none(self):
        """Test that None input raises ValueError."""
        transformer = CLRTransformer()
        
        with pytest.raises(ValueError):
            transformer.transform(None)

    def test_output_no_nan_inf(self):
        """Test that output contains no NaN or Inf values for valid input."""
        transformer = CLRTransformer()
        X = np.array([
            [0.965, 0.030, 0.005],
            [0.5, 0.25, 0.25]
        ])
        
        result = transformer.transform(X)
        
        assert not np.isnan(result).any()
        assert not np.isinf(result).any()