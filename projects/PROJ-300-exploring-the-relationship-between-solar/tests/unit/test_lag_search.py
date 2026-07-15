"""
Unit tests for the lag sweep logic in code/analysis/lag_search.py (FR-010).
Tests verify the window constraints and optimal lag identification.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def create_synthetic_lagged_data(n_points=1000, true_lag_minutes=45, noise_level=0.1):
    """
    Creates a synthetic dataset where Vsw and Ey have a known lag relationship.
    Ey is a delayed and noisy version of Vsw.
    """
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="1min")
    # Create a signal that looks somewhat like solar wind speed
    base_signal = np.sin(np.linspace(0, 20, n_points)) + 0.5 * np.cos(np.linspace(0, 10, n_points))
    # Add some random walk noise to make it realistic
    noise = np.cumsum(np.random.normal(0, 0.05, n_points))
    vsw = base_signal + noise
    vsw = vsw - np.min(vsw) + 300  # Shift to realistic range ~300-800 km/s

    # Create Ey as a delayed version of Vsw with noise
    # We shift the Vsw array by the true_lag_minutes
    lagged_vsw = np.roll(vsw, int(true_lag_minutes))
    # Handle the rolled part (wrap around) by filling with mean or just leaving the roll artifact for testing
    # For a clean test, we'll just use the rolled values but note that the start of the series is "wrapping"
    # A better simulation for testing lag detection:
    # Ey(t) = Vsw(t - true_lag) + noise
    # Since we are doing a discrete array, we simulate the delay by shifting indices
    
    # Let's create a cleaner correlation structure
    # Ey is highly correlated with Vsw shifted by true_lag
    ey = vsw.copy()
    # Shift the array to the right by true_lag_minutes (positive lag means Ey lags Vsw)
    # In numpy roll, positive shift moves elements to higher indices (right)
    # So Ey[i] = Vsw[i - lag]
    ey = np.roll(ey, int(true_lag_minutes))
    
    # Add noise to Ey
    ey = ey + np.random.normal(0, noise_level * np.std(vsw), n_points)

    df = pd.DataFrame({
        'timestamp': dates,
        'Vsw': vsw,
        'Ey': ey
    })
    return df


def test_lag_sweep_window():
    """
    Test that the lag sweep respects the configured window [LAG_WINDOW_MIN, LAG_WINDOW_MAX]
    and uses the correct step size.
    """
    # Create a dataset where the correlation is constant or random, just to check the window logic
    n_points = 500
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="1min")
    vsw = np.random.rand(n_points) * 100 + 400
    ey = np.random.rand(n_points) * 5 + 0.1
    
    df = pd.DataFrame({
        'timestamp': dates,
        'Vsw': vsw,
        'Ey': ey
    })

    # Run the sweep
    optimal_lag, correlation_value, lag_values, correlation_values = find_optimal_lag(df, 'Vsw', 'Ey')

    # Verify that all tested lags are within the window
    assert all(lag >= LAG_WINDOW_MIN for lag in lag_values), f"Lag values {lag_values} include values below {LAG_WINDOW_MIN}"
    assert all(lag <= LAG_WINDOW_MAX for lag in lag_values), f"Lag values {lag_values} include values above {LAG_WINDOW_MAX}"

    # Verify the step size is consistent (approximately)
    if len(lag_values) > 1:
        steps = np.diff(lag_values)
        # Allow small floating point variations if any, though they should be integers
        assert all(abs(s - LAG_STEP) < 1e-6 for s in steps), f"Lag steps {steps} do not match configured step {LAG_STEP}"

    # Verify the number of points in the sweep
    expected_count = (LAG_WINDOW_MAX - LAG_WINDOW_MIN) // LAG_STEP + 1
    assert len(lag_values) == expected_count, f"Expected {expected_count} lags, got {len(lag_values)}"


def test_optimal_lag_identification():
    """
    Test that the function correctly identifies the optimal lag when a strong
    correlation exists at a specific delay.
    """
    # Create synthetic data with a known true lag of 45 minutes
    true_lag = 45
    df = create_synthetic_lagged_data(n_points=1000, true_lag_minutes=true_lag, noise_level=0.05)

    # Run the sweep
    optimal_lag, correlation_value, lag_values, correlation_values = find_optimal_lag(df, 'Vsw', 'Ey')

    # The optimal lag should be close to the true lag (within a few minutes due to noise)
    # Given the strong correlation constructed, it should be very close.
    tolerance = 2  # minutes
    assert abs(optimal_lag - true_lag) <= tolerance, \
        f"Optimal lag {optimal_lag} is not within {tolerance} minutes of true lag {true_lag}"

    # Verify that the correlation at the optimal lag is the maximum absolute correlation
    # (Note: find_optimal_lag returns the lag that maximizes absolute correlation usually)
    # Let's check the correlation values returned
    max_abs_corr = np.max(np.abs(correlation_values))
    # The correlation at optimal_lag should be very close to max_abs_corr
    # We need to find the index of optimal_lag in lag_values
    try:
        idx = lag_values.index(optimal_lag)
        actual_corr = correlation_values[idx]
        assert abs(abs(actual_corr) - max_abs_corr) < 1e-6, \
            f"Correlation at optimal lag ({actual_corr}) is not the maximum ({max_abs_corr})"
    except ValueError:
        # If optimal_lag is not in lag_values (shouldn't happen), fail
        pytest.fail(f"Optimal lag {optimal_lag} not found in tested lags {lag_values}")


def test_optimal_lag_identification_with_negative_correlation():
    """
    Test that the function correctly identifies the optimal lag even if the
    relationship is negatively correlated.
    """
    # Create synthetic data with a known true lag
    true_lag = 60
    df = create_synthetic_lagged_data(n_points=1000, true_lag_minutes=true_lag, noise_level=0.05)
    
    # Invert Ey to create a negative correlation
    df['Ey'] = -df['Ey']

    # Run the sweep
    optimal_lag, correlation_value, lag_values, correlation_values = find_optimal_lag(df, 'Vsw', 'Ey')

    # The optimal lag should still be close to the true lag
    tolerance = 3
    assert abs(optimal_lag - true_lag) <= tolerance, \
        f"Optimal lag {optimal_lag} is not within {tolerance} minutes of true lag {true_lag} for negative correlation"

    # Verify the correlation is negative (since we inverted Ey)
    assert correlation_value < 0, f"Expected negative correlation, got {correlation_value}"


def test_lag_search_handles_nan_gracefully():
    """
    Test that the lag search handles NaN values in the input data without crashing.
    """
    n_points = 500
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="1min")
    vsw = np.random.rand(n_points) * 100 + 400
    ey = np.random.rand(n_points) * 5 + 0.1
    
    # Inject NaNs
    vsw[100:110] = np.nan
    ey[200:210] = np.nan
    
    df = pd.DataFrame({
        'timestamp': dates,
        'Vsw': vsw,
        'Ey': ey
    })

    # This should not raise an exception
    try:
        optimal_lag, correlation_value, lag_values, correlation_values = find_optimal_lag(df, 'Vsw', 'Ey')
    except Exception as e:
        pytest.fail(f"find_optimal_lag raised an exception with NaN data: {e}")

    # Verify we still got a result
    assert optimal_lag is not None
    assert isinstance(optimal_lag, (int, float))