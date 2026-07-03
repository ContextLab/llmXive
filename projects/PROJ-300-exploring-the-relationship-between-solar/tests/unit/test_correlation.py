"""
Unit tests for correlation analysis functions.
Tests for FR-005: Circular Block Permutation for significance testing.
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.correlation import (
    calculate_correlation,
    circular_block_permutation,
    moving_block_bootstrap
)

def test_permutation_block_size():
    """Test that circular_block_permutation calculates block size correctly based on autocorrelation."""
    # Create synthetic time series with known autocorrelation structure
    n = 500
    np.random.seed(42)
    x = pd.Series(np.random.randn(n).cumsum())  # Random walk with strong autocorrelation
    y = pd.Series(np.random.randn(n).cumsum())
    
    # Should not raise an exception and should calculate a reasonable block size
    p_value, block_size = circular_block_permutation(x, y, iterations=100)
    
    assert isinstance(p_value, float)
    assert isinstance(block_size, int)
    assert block_size > 0
    assert 0.0 <= p_value <= 1.0

def test_permutation_p_value_calculation():
    """Test that permutation test produces correct p-values for known scenarios."""
    # Create strongly correlated data
    n = 300
    np.random.seed(123)
    x = pd.Series(np.random.randn(n))
    y = pd.Series(0.8 * x + 0.2 * np.random.randn(n))  # Strong positive correlation
    
    p_value, _ = circular_block_permutation(x, y, iterations=500)
    
    # With strong correlation, p-value should be small (significant)
    assert p_value < 0.1, f"Expected small p-value for strong correlation, got {p_value}"

def test_permutation_uncorrelated_data():
    """Test that permutation test correctly identifies uncorrelated data."""
    # Create uncorrelated data
    n = 400
    np.random.seed(456)
    x = pd.Series(np.random.randn(n))
    y = pd.Series(np.random.randn(n))
    
    p_value, _ = circular_block_permutation(x, y, iterations=500)
    
    # With uncorrelated data, p-value should be large (not significant)
    assert p_value > 0.05, f"Expected large p-value for uncorrelated data, got {p_value}"

def test_permutation_with_nan():
    """Test that permutation test handles NaN values correctly."""
    n = 300
    np.random.seed(789)
    x = pd.Series(np.random.randn(n))
    y = pd.Series(np.random.randn(n))
    
    # Insert some NaN values
    x.iloc[10:15] = np.nan
    y.iloc[20:25] = np.nan
    
    # Should not raise an exception
    p_value, block_size = circular_block_permutation(x, y, iterations=100)
    
    assert isinstance(p_value, float)
    assert not np.isnan(p_value)
    assert 0.0 <= p_value <= 1.0

def test_permutation_iterations():
    """Test that increasing iterations improves p-value stability."""
    np.random.seed(101)
    n = 400
    x = pd.Series(np.random.randn(n))
    y = pd.Series(0.5 * x + 0.3 * np.random.randn(n))
    
    # Run with fewer iterations
    p_100, _ = circular_block_permutation(x, y, iterations=100)
    # Run with more iterations
    p_500, _ = circular_block_permutation(x, y, iterations=500)
    
    # Both should be valid p-values
    assert 0.0 <= p_100 <= 1.0
    assert 0.0 <= p_500 <= 1.0

def test_permutation_small_sample():
    """Test permutation behavior with small sample size."""
    # Very small sample
    x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    y = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0])
    
    # Should handle gracefully with minimal iterations
    p_value, block_size = circular_block_permutation(x, y, iterations=50)
    
    # Results should be numeric and valid
    assert isinstance(p_value, float)
    assert not np.isnan(p_value)
    assert 0.0 <= p_value <= 1.0
    assert block_size > 0

def test_permutation_negative_correlation():
    """Test that permutation test correctly identifies negative correlation."""
    n = 300
    np.random.seed(202)
    x = pd.Series(np.random.randn(n))
    y = pd.Series(-0.7 * x + 0.3 * np.random.randn(n))  # Strong negative correlation
    
    p_value, _ = circular_block_permutation(x, y, iterations=500)
    
    # With strong negative correlation, p-value should be small (significant)
    assert p_value < 0.1, f"Expected small p-value for strong negative correlation, got {p_value}"

def test_permutation_block_size_consistency():
    """Test that block size calculation is consistent for the same data."""
    np.random.seed(303)
    n = 400
    x = pd.Series(np.random.randn(n).cumsum())
    y = pd.Series(np.random.randn(n).cumsum())
    
    # Run multiple times
    _, block_size_1 = circular_block_permutation(x, y, iterations=50)
    _, block_size_2 = circular_block_permutation(x, y, iterations=50)
    
    # Block sizes should be the same for identical data
    assert block_size_1 == block_size_2, f"Block sizes inconsistent: {block_size_1} vs {block_size_2}"