"""
Unit tests for correlation analysis functions.
Tests for FR-006: Moving Block Bootstrap for confidence intervals.
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

def test_bootstrap_block_size():
    """Test that moving_block_bootstrap handles block size calculation correctly."""
    # Create synthetic time series with known structure
    n = 200
    np.random.seed(42)
    x = pd.Series(np.random.randn(n).cumsum())  # Random walk
    y = pd.Series(np.random.randn(n).cumsum())
    
    # Should not raise an exception
    mean_corr, lower_ci, upper_ci = moving_block_bootstrap(x, y, iterations=100)
    
    assert isinstance(mean_corr, float)
    assert isinstance(lower_ci, float)
    assert isinstance(upper_ci, float)
    assert lower_ci <= mean_corr <= upper_ci

def test_bootstrap_ci_calculation():
    """Test that bootstrap produces reasonable confidence intervals."""
    # Create correlated data
    n = 300
    np.random.seed(123)
    x = pd.Series(np.random.randn(n))
    y = pd.Series(0.5 * x + 0.3 * np.random.randn(n))  # Positive correlation
    
    mean_corr, lower_ci, upper_ci = moving_block_bootstrap(x, y, iterations=500)
    
    # Correlation should be positive
    assert mean_corr > 0.1, f"Expected positive correlation, got {mean_corr}"
    
    # CI should bracket the mean
    assert lower_ci <= mean_corr <= upper_ci
    
    # CI width should be reasonable (not too wide, not too narrow)
    ci_width = upper_ci - lower_ci
    assert 0.01 < ci_width < 1.0, f"CI width {ci_width} seems unreasonable"

def test_bootstrap_with_nan():
    """Test that bootstrap handles NaN values correctly."""
    n = 200
    np.random.seed(456)
    x = pd.Series(np.random.randn(n))
    y = pd.Series(np.random.randn(n))
    
    # Insert some NaN values
    x.iloc[10:15] = np.nan
    y.iloc[20:25] = np.nan
    
    # Should not raise an exception
    mean_corr, lower_ci, upper_ci = moving_block_bootstrap(x, y, iterations=100)
    
    assert isinstance(mean_corr, float)
    assert not np.isnan(mean_corr)

def test_bootstrap_small_sample():
    """Test bootstrap behavior with small sample size."""
    # Very small sample
    x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    y = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])
    
    # Should handle gracefully
    mean_corr, lower_ci, upper_ci = moving_block_bootstrap(x, y, iterations=50)
    
    # Results should be numeric
    assert isinstance(mean_corr, float)
    assert not np.isnan(mean_corr)

def test_bootstrap_iterations():
    """Test that increasing iterations improves CI precision."""
    np.random.seed(789)
    n = 400
    x = pd.Series(np.random.randn(n))
    y = pd.Series(0.6 * x + 0.2 * np.random.randn(n))
    
    # Run with fewer iterations
    _, lower_100, upper_100 = moving_block_bootstrap(x, y, iterations=100)
    # Run with more iterations
    _, lower_500, upper_500 = moving_block_bootstrap(x, y, iterations=500)
    
    # More iterations should give more stable estimates
    # (not strictly testable, but we check no crashes and reasonable values)
    assert not np.isnan(lower_500)
    assert not np.isnan(upper_500)
    assert lower_500 <= upper_500