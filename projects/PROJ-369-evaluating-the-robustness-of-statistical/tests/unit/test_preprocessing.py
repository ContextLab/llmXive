import pytest
import numpy as np
from statsmodels.tsa.stattools import adfuller
from src.data.preprocessing import check_stationarity_adf

# Test constants matching the project config (alpha=0.05)
ALPHA = 0.05
MIN_LENGTH = 25

def test_adf_stationary_series():
    """
    Test that a generated stationary series (e.g., white noise)
    is correctly identified as stationary (p-value < 0.05).
    """
    np.random.seed(42)
    # Generate white noise (stationary)
    data = np.random.normal(loc=0, scale=1, size=500)
    
    result = check_stationarity_adf(data)
    
    assert result['is_stationary'] is True, "White noise should be detected as stationary"
    assert result['p_value'] < ALPHA, f"p-value {result['p_value']} should be < {ALPHA}"
    assert result['statistic'] is not None
    assert result['critical_values'] is not None

def test_adf_non_stationary_series():
    """
    Test that a generated non-stationary series (random walk)
    is correctly identified as non-stationary (p-value >= 0.05).
    """
    np.random.seed(42)
    # Generate random walk (non-stationary)
    steps = np.random.normal(loc=0, scale=1, size=500)
    data = np.cumsum(steps)
    
    result = check_stationarity_adf(data)
    
    # Random walks are typically non-stationary in ADF tests
    assert result['is_stationary'] is False, "Random walk should be detected as non-stationary"
    assert result['p_value'] >= ALPHA, f"p-value {result['p_value']} should be >= {ALPHA}"

def test_adf_short_series_raises_error():
    """
    Test that a series shorter than the minimum length raises a ValueError.
    """
    np.random.seed(42)
    short_data = np.random.normal(loc=0, scale=1, size=10)
    
    with pytest.raises(ValueError) as excinfo:
        check_stationarity_adf(short_data)
    
    assert "too short" in str(excinfo.value).lower()
    assert str(MIN_LENGTH) in str(excinfo.value)

def test_adf_trend_series():
    """
    Test a series with a deterministic trend.
    Depending on the ADF model used (default includes trend),
    it might be stationary around the trend or non-stationary.
    Here we ensure the function runs and returns a valid structure.
    """
    np.random.seed(42)
    n = 500
    t = np.arange(n)
    trend = 0.1 * t
    noise = np.random.normal(loc=0, scale=1, size=n)
    data = trend + noise
    
    result = check_stationarity_adf(data)
    
    assert isinstance(result, dict)
    assert 'is_stationary' in result
    assert 'p_value' in result
    assert 'statistic' in result
    assert 'critical_values' in result

def test_adf_differenced_series():
    """
    Test that differencing a random walk makes it stationary.
    """
    np.random.seed(42)
    # Random walk
    steps = np.random.normal(loc=0, scale=1, size=500)
    rw = np.cumsum(steps)
    
    # Difference it
    diff_data = np.diff(rw)
    
    result = check_stationarity_adf(diff_data)
    
    assert result['is_stationary'] is True, "Differenced random walk should be stationary"
    assert result['p_value'] < ALPHA