"""
Unit tests for code/validate_era5.py
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import xarray as xr
import numpy as np
import pandas as pd

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_path))

from validate_era5 import (
    validate_hdf5_sample,
    SAMPLE_START_DATE,
    SAMPLE_END_DATE,
    SAMPLE_LAT,
    SAMPLE_LON
)

@pytest.fixture
def mock_h5_file(tmp_path):
    """Create a mock HDF5 file with valid ERA5-like data."""
    file_path = tmp_path / "mock_era5.h5"
    
    # Create a dataset matching expected structure
    # 7 days * 24 hours = 168 time steps
    time_steps = 168
    lat = [51.5074]
    lon = [-0.1278]
    
    times = pd.date_range(start="2016-01-01", periods=time_steps, freq="H")
    
    # Generate realistic temperature data (around 5°C with some variation)
    temp_k = 273.15 + 5 + np.random.normal(0, 2, time_steps)
    
    ds = xr.Dataset(
        {
            't2m': (['time', 'latitude', 'longitude'], 
                    temp_k.reshape(time_steps, 1, 1)),
        },
        coords={
            'time': times,
            'latitude': lat,
            'longitude': lon,
        }
    )
    
    ds.to_netcdf(file_path, engine='h5netcdf')
    return str(file_path)

def test_validate_hdf5_sample_correct_resolution(mock_h5_file):
    """Test that validation passes with correct hourly resolution."""
    is_valid, details = validate_hdf5_sample(mock_h5_file)
    
    assert is_valid is True
    assert any("Time resolution OK" in d for d in details)
    assert any("Temperature values valid" in d for d in details)

def test_validate_hdf5_sample_wrong_resolution(tmp_path):
    """Test that validation fails with incorrect time resolution."""
    file_path = tmp_path / "mock_wrong_time.h5"
    
    # Create dataset with wrong number of time steps (e.g., daily instead of hourly)
    times = pd.date_range(start="2016-01-01", periods=7, freq="D")
    temp_k = 278.15 * np.ones((7, 1, 1))
    
    ds = xr.Dataset(
        {
            't2m': (['time', 'latitude', 'longitude'], temp_k),
        },
        coords={
            'time': times,
            'latitude': [51.5074],
            'longitude': [-0.1278],
        }
    )
    
    ds.to_netcdf(file_path, engine='h5netcdf')
    
    is_valid, details = validate_hdf5_sample(str(file_path))
    
    assert is_valid is False
    assert any("Time resolution mismatch" in d for d in details)

def test_validate_hdf5_sample_out_of_range_temp(tmp_path):
    """Test that validation fails with impossible temperature values."""
    file_path = tmp_path / "mock_hot_temp.h5"
    
    time_steps = 168
    times = pd.date_range(start="2016-01-01", periods=time_steps, freq="H")
    
    # Impossible temperature: 100°C (373.15 K)
    temp_k = 373.15 * np.ones((time_steps, 1, 1))
    
    ds = xr.Dataset(
        {
            't2m': (['time', 'latitude', 'longitude'], temp_k),
        },
        coords={
            'time': times,
            'latitude': [51.5074],
            'longitude': [-0.1278],
        }
    )
    
    ds.to_netcdf(file_path, engine='h5netcdf')
    
    is_valid, details = validate_hdf5_sample(str(file_path))
    
    assert is_valid is False
    assert any("Temperature values out of expected range" in d for d in details)