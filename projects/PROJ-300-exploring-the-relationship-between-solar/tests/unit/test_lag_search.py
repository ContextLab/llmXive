"""
Unit tests for code/analysis/lag_search.py

Tests verify the lag sweep logic (FR-010) including:
- Correct search window generation
- Optimal lag identification
- Handling of edge cases (empty input, all-NaN)
- Custom window parameter handling
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def generate_test_data(n_points=1000, start_time=None, true_lag_minutes=45):
    """
    Helper to generate synthetic time series with a known lag relationship.
    
    Args:
        n_points: Number of data points to generate
        start_time: Starting timestamp (defaults to 2023-01-01)
        true_lag_minutes: Known lag in minutes between Vsw and Ey
    
    Returns:
        Tuple of (vsw_series, ey_series) as pandas Series with DatetimeIndex
    """
    if start_time is None:
        start_time = datetime(2023, 1, 1)
    
    # Generate timestamps at 5-minute cadence
    timestamps = [start_time + timedelta(minutes=i*5) for i in range(n_points)]
    
    # Create a base signal (sinusoidal with some variation)
    base_signal = np.sin(np.linspace(0, 10*np.pi, n_points))
    
    # Create Vsw with some noise
    vsw = base_signal + np.random.normal(0, 0.1, n_points)
    
    # Calculate lag in steps (5-minute cadence)
    lag_steps = int(true_lag_minutes / 5)
    
    # Create Ey that is Vsw shifted by the known lag + noise
    # Negative shift means Ey lags behind Vsw (Ey is shifted right in time)
    ey = np.roll(base_signal, -lag_steps) + np.random.normal(0, 0.1, n_points)
    
    # Handle the rolled-in values at the beginning (set to NaN)
    ey[:lag_steps] = np.nan
    
    vsw_series = pd.Series(vsw, index=pd.to_datetime(timestamps))
    ey_series = pd.Series(ey, index=pd.to_datetime(timestamps))
    
    return vsw_series, ey_series


def test_lag_sweep_window():
    """Test that the lag sweep covers the correct window with the right step size."""
    vsw, ey = generate_test_data(n_points=500)
    
    # Use a custom small window to verify exact values
    min_lag, max_lag, step = 30, 50, 5
    optimal_lag, max_corr, results = find_optimal_lag(
        vsw, ey, 
        min_lag=min_lag, 
        max_lag=max_lag, 
        step=step
    )
    
    # Verify results keys match the search window
    expected_lags = list(range(min_lag, max_lag + 1, step))
    assert list(results.keys()) == expected_lags, \
        f"Expected lags {expected_lags}, got {list(results.keys())}"
    
    # Verify the number of results matches the window
    expected_count = len(expected_lags)
    assert len(results) == expected_count, \
        f"Expected {expected_count} results, got {len(results)}"


def test_optimal_lag_identification():
    """Test that the function correctly identifies the optimal lag."""
    # Generate data with a known lag of 45 minutes
    true_lag = 45
    vsw, ey = generate_test_data(n_points=1000, true_lag_minutes=true_lag)
    
    # Search around the expected lag
    optimal_lag, max_corr, results = find_optimal_lag(
        vsw, ey, 
        min_lag=30, 
        max_lag=60, 
        step=5
    )
    
    # The optimal lag should be close to the true lag (allowing for noise)
    assert abs(optimal_lag - true_lag) <= 5, \
        f"Expected optimal lag near {true_lag}, got {optimal_lag}"
    
    # Verify that the max_corr corresponds to the optimal_lag in results
    assert abs(results[optimal_lag] - max_corr) < 1e-10, \
        f"max_corr {max_corr} does not match results[{optimal_lag}] {results[optimal_lag]}"
    
    # Verify that max_corr is the maximum value in results
    assert max_corr == max(results.values()), \
        f"max_corr {max_corr} is not the maximum in results"


def test_find_optimal_lag_basic():
    """Test that the function returns a valid lag within the search window."""
    vsw, ey = generate_test_data()
    
    optimal_lag, max_corr, results = find_optimal_lag(vsw, ey)
    
    # Check return types
    assert isinstance(optimal_lag, int), f"optimal_lag should be int, got {type(optimal_lag)}"
    assert isinstance(max_corr, float), f"max_corr should be float, got {type(max_corr)}"
    assert isinstance(results, dict), f"results should be dict, got {type(results)}"
    
    # Check lag is within default window
    assert LAG_WINDOW_MIN <= optimal_lag <= LAG_WINDOW_MAX, \
        f"optimal_lag {optimal_lag} outside default window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}]"
    
    # Check that max_corr is a valid correlation coefficient
    assert -1.0 <= max_corr <= 1.0, f"max_corr {max_corr} outside valid range [-1, 1]"


def test_find_optimal_lag_recovers_known_lag():
    """Test that the function can recover a known lag in synthetic data."""
    # Generate data with a known lag of 45 minutes (9 steps of 5 min)
    vsw, ey = generate_test_data(true_lag_minutes=45)
    
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
    
    assert optimal_lag in [30, 35], f"Expected 30 or 35, got {optimal_lag}"
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"


def test_find_optimal_lag_negative_correlation():
    """Test handling of data with negative correlation."""
    # Generate data with negative correlation
    timestamps = pd.date_range(start='2023-01-01', periods=500, freq='5min')
    base_signal = np.sin(np.linspace(0, 10*np.pi, 500))
    vsw = base_signal + np.random.normal(0, 0.1, 500)
    # Invert the signal for negative correlation
    ey = -np.roll(base_signal, -9) + np.random.normal(0, 0.1, 500)
    ey[:9] = np.nan
    
    vsw_series = pd.Series(vsw, index=timestamps)
    ey_series = pd.Series(ey, index=timestamps)
    
    optimal_lag, max_corr, results = find_optimal_lag(
        vsw_series, ey_series,
        min_lag=30,
        max_lag=60,
        step=5
    )
    
    # Should still find an optimal lag, even if correlation is negative
    assert LAG_WINDOW_MIN <= optimal_lag <= LAG_WINDOW_MAX
    # max_corr should be the maximum (least negative) correlation
    assert max_corr == max(results.values())


def test_find_optimal_lag_single_point_valid():
    """Test that the function handles minimal valid input."""
    # Create minimal valid dataset with at least 2 points after lag
    timestamps = pd.date_range(start='2023-01-01', periods=20, freq='5min')
    vsw = pd.Series(np.random.randn(20), index=timestamps)
    ey = pd.Series(np.random.randn(20), index=timestamps)
    
    # Use a very narrow window
    optimal_lag, max_corr, results = find_optimal_lag(
        vsw, ey,
        min_lag=30,
        max_lag=35,
        step=5
    )
    
    assert optimal_lag in [30, 35]
    assert -1.0 <= max_corr <= 1.0