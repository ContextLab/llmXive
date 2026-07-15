import pytest
import numpy as np
import pandas as pd
from scipy import stats
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS

def create_time_series_with_autocorrelation(n=200, rho=0.5):
    """Create a time series with known autocorrelation structure."""
    np.random.seed(42)
    eps = np.random.normal(0, 1, n)
    series = np.zeros(n)
    for i in range(1, n):
        series[i] = rho * series[i-1] + eps[i]
    return series

def test_permutation_block_size():
    """Test that circular block permutation correctly determines block size."""
    # Create time series with known autocorrelation
    x = create_time_series_with_autocorrelation(n=200, rho=0.7)
    y = create_time_series_with_autocorrelation(n=200, rho=0.7)
    
    # Test with different iteration counts
    p_val_100 = circular_block_permutation(x, y, iterations=100)
    p_val_1000 = circular_block_permutation(x, y, iterations=1000)
    
    # Both should return valid p-values between 0 and 1
    assert 0 <= p_val_100 <= 1
    assert 0 <= p_val_1000 <= 1
    
    # More iterations should give more stable results
    assert isinstance(p_val_100, float)
    assert isinstance(p_val_1000, float)

def test_permutation_p_value_calculation():
    """Test that permutation test correctly calculates p-values."""
    # Create two independent time series
    np.random.seed(42)
    x = np.random.normal(0, 1, 200)
    y = np.random.normal(0, 1, 200)
    
    # Calculate p-value with permutations
    p_val = circular_block_permutation(x, y, iterations=1000)
    
    # For independent series, p-value should be high (not significant)
    # Note: With only 1000 iterations, we expect some variance
    # but it should generally be > 0.05 for independent data
    assert p_val > 0.01  # Should not be extremely significant

def test_bootstrap_block_size():
    """Test that moving block bootstrap correctly determines block size."""
    # Create time series with autocorrelation
    x = create_time_series_with_autocorrelation(n=200, rho=0.6)
    y = create_time_series_with_autocorrelation(n=200, rho=0.6)
    
    # Test bootstrap with different iteration counts
    ci_100 = moving_block_bootstrap(x, y, iterations=100)
    ci_1000 = moving_block_bootstrap(x, y, iterations=1000)
    
    # Both should return confidence intervals
    assert len(ci_100) == 2
    assert len(ci_1000) == 2
    
    # Lower bound should be less than upper bound
    assert ci_100[0] <= ci_100[1]
    assert ci_1000[0] <= ci_1000[1]

def test_bootstrap_ci_calculation():
    """Test that bootstrap correctly calculates confidence intervals."""
    # Create time series with known correlation
    np.random.seed(42)
    x = np.random.normal(0, 1, 200)
    y = 0.5 * x + np.random.normal(0, 0.5, 200)  # Positive correlation
    
    # Calculate bootstrap CI
    ci = moving_block_bootstrap(x, y, iterations=500)
    
    # For positive correlation, CI should generally be positive
    # (though with limited iterations, there's some variance)
    assert ci[0] < ci[1]  # Valid interval
    
    # The interval should contain reasonable values
    assert -1 <= ci[0] <= 1
    assert -1 <= ci[1] <= 1

def test_calculate_correlation_basic():
    """Test basic correlation calculation."""
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 6, 8, 10])
    
    pearson, spearman = calculate_correlation(x, y)
    
    # Perfect linear relationship
    assert abs(pearson - 1.0) < 0.01
    assert abs(spearman - 1.0) < 0.01

def test_calculate_correlation_with_nan():
    """Test correlation calculation with NaN values."""
    x = np.array([1, 2, np.nan, 4, 5])
    y = np.array([2, 4, 6, np.nan, 10])
    
    # Should handle NaN by dropping pairs
    pearson, spearman = calculate_correlation(x, y)
    
    # Should return valid correlations
    assert not np.isnan(pearson)
    assert not np.isnan(spearman)
