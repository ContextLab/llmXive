"""
Unit tests for lag sweep logic in code/analysis/lag_search.py.
Tests FR-010: find_optimal_lag function.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path if running from tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def create_synthetic_lagged_dataset(n_samples=1000, true_lag_minutes=45, noise_level=0.3):
    """
    Create a synthetic dataset where Ey is correlated with Vsw shifted by true_lag_minutes.
    This allows testing if find_optimal_lag can recover the known lag.
    """
    # Create timestamps
    start_time = datetime(2023, 1, 1)
    timestamps = [start_time + timedelta(minutes=i*5) for i in range(n_samples)]
    
    # Create Vsw with some trend and noise
    vsw_base = 400 + 100 * np.sin(np.linspace(0, 4*np.pi, n_samples))
    vsw_noise = np.random.normal(0, 20, n_samples)
    vsw = vsw_base + vsw_noise
    
    # Create Ey with correlation to shifted Vsw
    # Shift index by true_lag_minutes / 5 (since data is 5-min cadence)
    lag_index = int(true_lag_minutes / 5)
    shifted_vsw = np.roll(vsw, lag_index)
    
    # Ey = 0.5 * shifted_Vsw + noise
    ey_base = 0.5 * shifted_vsw
    ey_noise = np.random.normal(0, noise_level * 100, n_samples)
    ey = ey_base + ey_noise
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw,
        'Ey': ey
    })
    
    return df


def test_lag_sweep_window():
    """
    Test that the lag sweep covers the expected window [LAG_WINDOW_MIN, LAG_WINDOW_MAX]
    with step size LAG_STEP.
    """
    # Create a simple dataset
    df = create_synthetic_lagged_dataset(n_samples=200, true_lag_minutes=50)
    
    # Run the lag sweep
    results = find_optimal_lag(df['Vsw'], df['Ey'])
    
    # Verify the results contain lag candidates in the expected range
    lag_candidates = results['lag_candidates']
    
    assert len(lag_candidates) > 0, "No lag candidates generated"
    
    # Check that all candidates are within the expected window
    for lag in lag_candidates:
        assert LAG_WINDOW_MIN <= lag <= LAG_WINDOW_MAX, \
            f"Lag {lag} outside expected window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}]"
    
    # Check that the step size is approximately correct
    if len(lag_candidates) > 1:
        steps = np.diff(lag_candidates)
        # Allow some tolerance for floating point
        assert all(abs(step - LAG_STEP) < 0.1 for step in steps), \
            f"Lag steps {steps} do not match expected step size {LAG_STEP}"


def test_optimal_lag_identification():
    """
    Test that find_optimal_lag correctly identifies the optimal lag
    when there is a known correlation at a specific lag.
    """
    # Create a dataset with a known true lag of 45 minutes
    true_lag = 45
    df = create_synthetic_lagged_dataset(n_samples=500, true_lag_minutes=true_lag)
    
    # Run the lag sweep
    results = find_optimal_lag(df['Vsw'], df['Ey'])
    
    # Verify the optimal lag is close to the true lag
    optimal_lag = results['optimal_lag']
    optimal_corr = results['optimal_correlation']
    
    # The optimal lag should be within ±1 minute of the true lag
    # (accounting for step size and noise)
    assert abs(optimal_lag - true_lag) <= (LAG_STEP + 1), \
        f"Optimal lag {optimal_lag} too far from true lag {true_lag}"
    
    # The optimal correlation should be the maximum absolute correlation
    abs_corrs = [abs(c) for c in results['correlations']]
    max_abs_corr = max(abs_corrs)
    
    assert abs(optimal_corr) == max_abs_corr, \
        f"Optimal correlation {optimal_corr} is not the maximum absolute correlation {max_abs_corr}"
    
    # Verify that the optimal lag corresponds to the optimal correlation
    lag_idx = results['lag_candidates'].index(optimal_lag)
    assert abs(results['correlations'][lag_idx]) == max_abs_corr, \
        "Optimal lag does not correspond to maximum correlation"


def test_optimal_lag_with_negative_correlation():
    """
    Test that find_optimal_lag correctly handles negative correlations.
    """
    # Create a dataset with negative correlation
    n_samples = 500
    start_time = datetime(2023, 1, 1)
    timestamps = [start_time + timedelta(minutes=i*5) for i in range(n_samples)]
    
    vsw = 400 + 100 * np.sin(np.linspace(0, 4*np.pi, n_samples)) + np.random.normal(0, 20, n_samples)
    
    # Create Ey with negative correlation to shifted Vsw
    lag_index = int(60 / 5)  # 60 minute lag
    shifted_vsw = np.roll(vsw, lag_index)
    ey = -0.5 * shifted_vsw + np.random.normal(0, 50, n_samples)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw,
        'Ey': ey
    })
    
    # Run the lag sweep
    results = find_optimal_lag(df['Vsw'], df['Ey'])
    
    # The optimal correlation should be negative
    assert results['optimal_correlation'] < 0, \
        f"Expected negative correlation for negatively correlated data, got {results['optimal_correlation']}"
    
    # The optimal lag should be close to 60 minutes
    assert abs(results['optimal_lag'] - 60) <= (LAG_STEP + 1), \
        f"Optimal lag {results['optimal_lag']} too far from expected 60 minutes"


def test_find_optimal_lag_empty_input():
    """
    Test that find_optimal_lag handles empty input gracefully.
    """
    empty_vsw = pd.Series([])
    empty_ey = pd.Series([])
    
    with pytest.raises((ValueError, IndexError)):
        find_optimal_lag(empty_vsw, empty_ey)


def test_find_optimal_lag_single_value():
    """
    Test that find_optimal_lag handles single-value input gracefully.
    """
    single_vsw = pd.Series([400.0])
    single_ey = pd.Series([50.0])
    
    with pytest.raises((ValueError, IndexError)):
        find_optimal_lag(single_vsw, single_ey)


def test_find_optimal_lag_with_nans():
    """
    Test that find_optimal_lag handles NaN values correctly.
    """
    # Create dataset with some NaN values
    df = create_synthetic_lagged_dataset(n_samples=200, true_lag_minutes=45)
    
    # Introduce some NaN values
    df.loc[10:15, 'Vsw'] = np.nan
    df.loc[20:25, 'Ey'] = np.nan
    
    # This should not raise an error, but the function should handle NaNs
    # (either by filtering or by the underlying correlation function)
    try:
        results = find_optimal_lag(df['Vsw'], df['Ey'])
        # If it succeeds, verify the results are reasonable
        assert 'optimal_lag' in results
        assert 'optimal_correlation' in results
    except Exception as e:
        # If it fails, it should be due to insufficient valid data
        # This is acceptable behavior
        assert "not enough valid data" in str(e).lower() or "insufficient" in str(e).lower()