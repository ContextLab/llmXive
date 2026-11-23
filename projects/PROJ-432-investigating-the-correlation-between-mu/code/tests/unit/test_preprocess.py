import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.preprocess import calculate_t_eff, pressure_to_altitude, calculate_weight_function

@pytest.fixture
def sample_long_data():
    """
    Creates a sample DataFrame in long format (one row per date-pressure).
    Simulates a 2-day profile with standard pressures.
    """
    dates = pd.date_range(start='2023-01-01', periods=2, freq='D')
    pressures = [1000, 850, 700, 500, 300, 200, 100]
    
    data = []
    for date in dates:
        for p in pressures:
            # Simulate temperature decreasing with altitude (approx)
            # T ~ 288 - 6.5 * h(km)
            h = pressure_to_altitude(p)
            t = 288.15 - 6.5 * h + np.random.normal(0, 0.1) # Add small noise
            data.append({'date': date, 'pressure_level': p, 'temperature': t})
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_missing_data():
    """
    Creates data with a missing pressure level for one date.
    """
    dates = pd.date_range(start='2023-01-01', periods=2, freq='D')
    pressures = [1000, 850, 700, 500, 300, 200, 100]
    
    data = []
    for i, date in enumerate(dates):
        # For the second date, skip 300 hPa
        current_pressures = pressures if i == 0 else [p for p in pressures if p != 300]
        for p in current_pressures:
            h = pressure_to_altitude(p)
            t = 288.15 - 6.5 * h
            data.append({'date': date, 'pressure_level': p, 'temperature': t})
    
    return pd.DataFrame(data)

def test_get_pressure_altitude():
    """Test the pressure to altitude conversion."""
    # At 1013.25 hPa, altitude should be ~0
    h = pressure_to_altitude(1013.25)
    assert abs(h) < 0.01
    
    # At 500 hPa, altitude should be ~5.5 km
    h = pressure_to_altitude(500)
    assert 5.0 < h < 6.0

def test_calculate_t_eff_single_day(sample_long_data):
    """Test T_eff calculation on a single day (subset)."""
    single_day = sample_long_data[sample_long_data['date'] == sample_long_data['date'].iloc[0]]
    result = calculate_t_eff(single_day)
    
    assert len(result) == 1
    assert not pd.isna(result.iloc[0])
    # T_eff should be a reasonable atmospheric temperature (e.g., between 200K and 300K)
    assert 200 < result.iloc[0] < 300

def test_calculate_t_eff_interpolation(sample_missing_data):
    """Test that missing pressure levels are interpolated."""
    result = calculate_t_eff(sample_missing_data)
    
    # Should have 2 entries
    assert len(result) == 2
    
    # Both should be non-null (interpolation should fill the gap)
    assert not pd.isna(result.iloc[0])
    assert not pd.isna(result.iloc[1])
    
    # The value for the day with missing data should be close to the day with full data
    # (since the temperature profile is smooth)
    diff = abs(result.iloc[0] - result.iloc[1])
    assert diff < 5.0 # Allow some difference due to profile variation, but not huge

def test_calculate_t_eff_missing_data():
    """Test behavior when data is completely missing for a date."""
    df = pd.DataFrame({'date': ['2023-01-01'], 'pressure_level': [500], 'temperature': [np.nan]})
    result = calculate_t_eff(df)
    assert pd.isna(result.iloc[0])

def test_calculate_t_eff_empty():
    """Test behavior on empty dataframe."""
    df = pd.DataFrame(columns=['date', 'pressure_level', 'temperature'])
    result = calculate_t_eff(df)
    assert len(result) == 0

def test_calculate_t_eff_insufficient_points():
    """Test behavior with only one pressure level (cannot interpolate)."""
    df = pd.DataFrame({'date': ['2023-01-01'], 'pressure_level': [500], 'temperature': [250.0]})
    result = calculate_t_eff(df)
    # Should return NaN because we need at least 2 points for linear interpolation
    assert pd.isna(result.iloc[0])
