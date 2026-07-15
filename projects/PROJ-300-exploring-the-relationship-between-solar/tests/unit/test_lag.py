"""
Unit tests for code/data/lag.py
Tests for FR-012: Physics-based lag calculation and application.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.lag import calculate_physics_lag, apply_lag_shift, prepare_lagged_data
from code.config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE

def test_lag_calculation_formula():
    """
    Test the physics-based lag calculation.
    Formula derived from FR-012:
    Distance = TAIL_DISTANCE_RE * EARTH_RADIUS_KM (km)
    Time (s) = Distance / Vsw (km/s)
    Time (min) = Time (s) / 60

    L_phys = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / Vsw / 60

    With constants: TAIL_DISTANCE_RE=60, EARTH_RADIUS_KM=6371
    L_phys = (60 * 6371) / Vsw / 60 = 6371 / Vsw
    """
    vsw = 400.0  # km/s
    # Expected: (60 * 6371) / 400 / 60 = 15.9275
    expected_lag = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / vsw / 60.0

    result = calculate_physics_lag(vsw)
    assert abs(result - expected_lag) < 1e-5, f"Expected {expected_lag}, got {result}"

def test_lag_calculation_high_speed():
    """Test with high solar wind speed (800 km/s) -> shorter lag."""
    vsw = 800.0
    result = calculate_physics_lag(vsw)
    expected = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / vsw / 60.0
    assert abs(result - expected) < 1e-5

def test_lag_calculation_low_speed():
    """Test with low solar wind speed (300 km/s) -> longer lag."""
    vsw = 300.0
    result = calculate_physics_lag(vsw)
    expected = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / vsw / 60.0
    assert abs(result - expected) < 1e-5

def test_lag_calculation_invalid_speed():
    """Test that zero or negative speed raises an error."""
    with pytest.raises(ValueError):
        calculate_physics_lag(0.0)
    with pytest.raises(ValueError):
        calculate_physics_lag(-100.0)

def test_lag_shift_applies_correctly():
    """Test that apply_lag_shift correctly shifts the time index."""
    # Create a simple DataFrame with DatetimeIndex
    dates = pd.date_range(start='2023-01-01', periods=5, freq='H')
    df = pd.DataFrame({'value': [1, 2, 3, 4, 5]}, index=dates)

    lag_minutes = 30.0
    df_shifted = apply_lag_shift(df, lag_minutes)

    # Check that the index has shifted
    original_first = df.index[0]
    shifted_first = df_shifted.index[0]

    expected_first = original_first + pd.Timedelta(minutes=lag_minutes)
    assert shifted_first == expected_first, f"Expected {expected_first}, got {shifted_first}"

    # Check values are preserved
    assert df_shifted['value'].tolist() == [1, 2, 3, 4, 5]

def test_prepare_lagged_data_integration():
    """Test the full pipeline of calculating lag and shifting data."""
    # Create synthetic solar wind data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='10T')
    vsw_values = np.full(100, 400.0) # Constant 400 km/s
    df_sw = pd.DataFrame({'Vsw': vsw_values}, index=dates)

    # Create synthetic Ey data
    ey_values = np.random.randn(100)
    df_ey = pd.DataFrame({'Ey': ey_values}, index=dates)

    df_sw_shifted, df_ey_out, lag = prepare_lagged_data(df_sw, df_ey)

    # Verify lag calculation
    expected_lag = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / 400.0 / 60.0
    assert abs(lag - expected_lag) < 1e-5

    # Verify shift
    original_first = df_sw.index[0]
    shifted_first = df_sw_shifted.index[0]
    expected_shifted = original_first + pd.Timedelta(minutes=lag)
    assert shifted_first == expected_shifted

    # Verify Ey is unchanged (no shift applied to Ey in this function)
    assert df_ey_out.index.equals(df_ey.index)

def test_prepare_lagged_data_with_nan():
    """Test handling of NaN values in Vsw calculation."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='10T')
    vsw_values = np.full(100, 400.0)
    vsw_values[10] = np.nan # Introduce a NaN
    df_sw = pd.DataFrame({'Vsw': vsw_values}, index=dates)

    df_ey = pd.DataFrame({'Ey': np.random.randn(100)}, index=dates)

    # Should not raise an error
    df_sw_shifted, df_ey_out, lag = prepare_lagged_data(df_sw, df_ey)

    # Lag should be calculated based on mean of valid values (which is 400.0)
    expected_lag = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / 400.0 / 60.0
    assert abs(lag - expected_lag) < 1e-5

def test_prepare_lagged_data_all_nan():
    """Test handling when all Vsw values are NaN."""
    dates = pd.date_range(start='2023-01-01', periods=10, freq='H')
    df_sw = pd.DataFrame({'Vsw': [np.nan] * 10}, index=dates)
    df_ey = pd.DataFrame({'Ey': np.random.randn(10)}, index=dates)

    with pytest.raises(ValueError):
        prepare_lagged_data(df_sw, df_ey)

def test_prepare_lagged_data_missing_column():
    """Test that missing Vsw column raises an error."""
    dates = pd.date_range(start='2023-01-01', periods=10, freq='H')
    df_sw = pd.DataFrame({'Bz': np.random.randn(10)}, index=dates)
    df_ey = pd.DataFrame({'Ey': np.random.randn(10)}, index=dates)

    with pytest.raises(ValueError):
        prepare_lagged_data(df_sw, df_ey)

def test_apply_lag_shift_non_datetime_index():
    """Test that apply_lag_shift raises an error for non-DatetimeIndex."""
    df = pd.DataFrame({'value': [1, 2, 3]})
    with pytest.raises(TypeError):
        apply_lag_shift(df, 30.0)