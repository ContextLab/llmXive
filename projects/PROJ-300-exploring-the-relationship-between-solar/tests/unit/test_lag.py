"""
Unit tests for code/data/lag.py
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

def test_lag_calculation_formula():
    """
    Test the physics-based lag calculation.
    Formula: L_phys = (60 * 6371) / Vsw_mean / 60
    Simplified: L_phys = 6371 / Vsw_mean
    Wait, let's re-read the formula in the task:
    L_phys = (k * 6371) / Vsw_mean / k  -> The 'k' cancels out?
    Actually, the task description says: "L_phys = (k * 6371) / Vsw_mean / k"
    And "Ensure the code correctly handles the unit conversion (km/s to minutes) and includes the 60 factor."
    
    The physical distance is 60 RE. So Distance = 60 * 6371 km.
    Time (seconds) = Distance / Vsw (km/s)
    Time (minutes) = Time (seconds) / 60
    
    So L_phys = (60 * 6371) / Vsw / 60 = 6371 / Vsw.
    
    Let's verify with a known value.
    If Vsw = 400 km/s.
    Distance = 60 * 6371 = 382260 km.
    Time (s) = 382260 / 400 = 955.65 s.
    Time (min) = 955.65 / 60 = 15.9275 min.
    
    Using simplified formula: 6371 / 400 = 15.9275 min.
    Matches.
    """
    vsw = 400.0  # km/s
    expected_lag = 6371.0 / vsw  # 15.9275 minutes
    
    result = calculate_physics_lag(vsw)
    assert abs(result - expected_lag) < 1e-5, f"Expected {expected_lag}, got {result}"

def test_lag_calculation_high_speed():
    """Test with high solar wind speed (800 km/s) -> shorter lag."""
    vsw = 800.0
    result = calculate_physics_lag(vsw)
    # 6371 / 800 = 7.96375
    expected = 6371.0 / 800.0
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
    expected_lag = 6371.0 / 400.0
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
    expected_lag = 6371.0 / 400.0
    assert abs(lag - expected_lag) < 1e-5