"""
Unit tests for lag calculation and shifting.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from code.data.lag import calculate_physics_lag, apply_lag_shift

def test_lag_calculation_formula():
    """Test that calculate_physics_lag uses the correct formula: 6371 / vsw_mean."""
    vsw = 400.0  # km/s
    expected_lag = 6371.0 / vsw
    calculated_lag = calculate_physics_lag(vsw)

    assert abs(calculated_lag - expected_lag) < 1e-6

def test_lag_shift_applies_correctly():
    """Test that apply_lag_shift shifts the series by the correct number of periods."""
    # Create a 5-minute cadence series
    dates = pd.date_range(start='2023-01-01', periods=10, freq='5min')
    values = np.arange(10, dtype=float)
    series = pd.Series(values, index=dates)

    # Shift by 15 minutes (3 periods)
    lag_minutes = 15
    shifted = apply_lag_shift(series, lag_minutes)

    # Check that the first 3 values are NaN
    assert pd.isna(shifted.iloc[0])
    assert pd.isna(shifted.iloc[1])
    assert pd.isna(shifted.iloc[2])

    # Check that the 4th value is the original first value
    assert shifted.iloc[3] == values[0]
    
    # Check that the last value is NaN (shifted out)
    assert pd.isna(shifted.iloc[-1])