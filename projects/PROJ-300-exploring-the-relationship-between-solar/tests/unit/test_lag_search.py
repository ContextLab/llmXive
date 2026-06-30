"""
Unit tests for code/analysis/lag_search.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def generate_test_data(n_points=1000, start_time=None):
    """Helper to generate synthetic time series with a known lag relationship."""
    if start_time is None:
        start_time = datetime(2023, 1, 1)
    
    timestamps = [start_time + timedelta(minutes=i*5) for i in range(n_points)]
    # Create a base signal
    base_signal = np.sin(np.linspace(0, 10*np.pi, n_points))
    
    # Create Vsw with some noise
    vsw = base_signal + np.random.normal(0, 0.1, n_points)
    
    # Create Ey that is Vsw shifted by a known lag (e.g., 45 minutes) + noise
    # Since 5 min cadence, 45 min lag = 9 steps
    lag_steps = 9
    ey = np.roll(base_signal, -lag_steps) + np.random.normal(0, 0.1, n_points)
    
    # Handle the rolled-in NaNs at the end
    ey[:lag_steps] = np.nan
    
    return pd.Series(vsw, index=pd.to_datetime(timestamps)), \
           pd.Series(ey, index=pd.to_datetime(timestamps))


def test_find_optimal_lag_basic():
    """Test that the function returns a valid lag within the search window."""
    vsw, ey = generate_test_data()
    
    optimal_lag, max_corr, results = find_optimal_lag(vsw, ey)
    
    # Check return types
    assert isinstance(optimal_lag, int)
    assert isinstance(max_corr, float)
    assert isinstance(results, dict)
    
    # Check lag is within default window
    assert LAG_WINDOW_MIN <= optimal_lag <= LAG_WINDOW_MAX
    
    # Check that max_corr is positive
    assert max_corr > 0


def test_find_optimal_lag_recovers_known_lag():
    """Test that the function can recover a known lag in synthetic data."""
    # Generate data with a known lag of 45 minutes (9 steps of 5 min)
    vsw, ey = generate_test_data()
    
    # Search specifically around the expected lag to avoid edge effects
    optimal_lag, max_corr, results = find_optimal_lag(
        vsw, ey, 
        min_lag=30, 
        max_lag=60, 
        step=5
    )
    
    # The optimal lag should be close to 45 minutes (allowing for noise)
    assert 40 <= optimal_lag <= 50, f"Expected lag near 45, got {optimal_lag}"


def test_find_optimal_lag_empty_input():
    """Test that the function raises an error for empty input."""
    vsw = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
    ey = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
    
    with pytest.raises(ValueError, match="Input series cannot be empty"):
        find_optimal_lag(vsw, ey)


def test_find_optimal_lag_all_nan():
    """Test behavior when one series is all NaN."""
    timestamps = pd.date_range(start='2023-01-01', periods=100, freq='5min')
    vsw = pd.Series(np.random.randn(100), index=timestamps)
    ey = pd.Series(np.nan, index=timestamps)
    
    with pytest.raises(ValueError, match="No valid correlations found"):
        find_optimal_lag(vsw, ey)


def test_find_optimal_lag_custom_window():
    """Test that custom window parameters are respected."""
    vsw, ey = generate_test_data()
    
    # Search a narrow window
    optimal_lag, max_corr, results = find_optimal_lag(
        vsw, ey,
        min_lag=30,
        max_lag=35,
        step=5
    )
    
    assert optimal_lag in [30, 35]
    assert len(results) == 2  # Only 30 and 35 should be in results