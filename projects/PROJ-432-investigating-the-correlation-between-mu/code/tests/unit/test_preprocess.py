import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.preprocess import calculate_t_eff, _get_pressure_altitude

def test_get_pressure_altitude():
    """Test the barometric formula conversion."""
    # At surface (1013.25 hPa), altitude should be ~0
    z = _get_pressure_altitude(1013.25)
    assert np.isclose(z, 0.0, atol=0.01)
    
    # At 500 hPa, altitude should be approx 5.5 km (standard atmosphere)
    # H = 7.64, z = -7.64 * ln(500/1013.25) = -7.64 * ln(0.493) = -7.64 * -0.707 = 5.4
    z_500 = _get_pressure_altitude(500)
    assert 5.0 < z_500 < 6.0

def test_calculate_t_eff_single_day():
    """Test T_eff calculation with a simple synthetic profile."""
    # Create synthetic data for one day
    # Pressure levels: 1000, 850, 700, 500, 300, 100 hPa
    # Temperature: decreasing with height (linear approx)
    dates = ['2023-01-01'] * 6
    pressures = [1000, 850, 700, 500, 300, 100]
    # Approx temp: 288K at surface, lapse rate ~6.5K/km
    # z ~ 0 -> 288
    # z ~ 1.5 -> 278
    # z ~ 3.0 -> 268
    # z ~ 5.4 -> 252
    # z ~ 9.0 -> 230
    # z ~ 16 -> 180
    temps = [288, 278, 268, 252, 230, 180]
    
    df = pd.DataFrame({
        'date': dates,
        'pressure': pressures,
        'temperature': temps
    })
    
    t_eff = calculate_t_eff(df)
    
    assert len(t_eff) == 1
    assert '2023-01-01' in t_eff.index
    # T_eff should be a reasonable weighted average, likely closer to lower atmosphere temps
    # because muon production peaks lower (13km) but weight is spread.
    # With our parameters (z_peak=13), the weight is significant at 13km.
    # 100hPa is ~16km. 300hPa is ~9km.
    # The value should be between 180 and 288.
    val = t_eff['2023-01-01']
    assert 180 < val < 288

def test_calculate_t_eff_interpolation():
    """Test that linear interpolation handles sparse data correctly."""
    # Sparse data: only 1000 hPa and 100 hPa
    dates = ['2023-01-02'] * 2
    pressures = [1000, 100]
    temps = [288, 180]
    
    df = pd.DataFrame({
        'date': dates,
        'pressure': pressures,
        'temperature': temps
    })
    
    t_eff = calculate_t_eff(df)
    
    assert len(t_eff) == 1
    # Should not crash and should produce a value
    val = t_eff['2023-01-02']
    assert 180 < val < 288

def test_calculate_t_eff_missing_data():
    """Test handling of missing values."""
    dates = ['2023-01-03'] * 4
    pressures = [1000, 850, np.nan, 500]
    temps = [288, 278, 268, 252]
    
    df = pd.DataFrame({
        'date': dates,
        'pressure': pressures,
        'temperature': temps
    })
    
    # Should drop the NaN row and calculate with remaining 3
    t_eff = calculate_t_eff(df)
    assert len(t_eff) == 1

def test_calculate_t_eff_empty():
    """Test handling of empty dataframe."""
    df = pd.DataFrame(columns=['date', 'pressure', 'temperature'])
    t_eff = calculate_t_eff(df)
    assert len(t_eff) == 0

def test_calculate_t_eff_insufficient_points():
    """Test handling of single point (cannot interpolate/integrate)."""
    dates = ['2023-01-04']
    pressures = [1000]
    temps = [288]
    
    df = pd.DataFrame({
        'date': dates,
        'pressure': pressures,
        'temperature': temps
    })
    
    t_eff = calculate_t_eff(df)
    # Should return empty or handle gracefully
    # Our implementation logs warning and continues, resulting in empty for that date
    assert len(t_eff) == 0
