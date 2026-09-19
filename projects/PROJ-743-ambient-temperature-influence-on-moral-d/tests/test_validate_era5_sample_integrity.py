"""
Unit tests for T004: validate_era5_sample_integrity.
"""
import pytest
import os
import sys
import tempfile
import h5py
import numpy as np
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from validate_era5_sample_integrity import (
    validate_temporal_resolution,
    validate_grid_size,
    validate_temperature_range
)

@pytest.fixture
def mock_hdf5_file():
    """Create a temporary HDF5 file with mock ERA5-like data."""
    fd, path = tempfile.mkstemp(suffix='.h5')
    os.close(fd)
    
    with h5py.File(path, 'w') as hf:
        # Create time dimension (hourly for 7 days)
        time_data = np.arange(0, 7 * 24, 1) # 0 to 167 hours
        hf.create_dataset('time', data=time_data)

        # Create lat/lon grid (0.25 deg)
        lat_data = np.arange(-90, 90.25, 0.25)
        lon_data = np.arange(-180, 180.25, 0.25)
        hf.create_dataset('latitude', data=lat_data)
        hf.create_dataset('longitude', data=lon_data)

        # Create temperature data (2m temperature, Kelvin in reality, but we'll store C for this test)
        # Shape: (time, lat, lon)
        temp_data = np.random.normal(288.0, 10.0, (len(time_data), len(lat_data), len(lon_data)))
        # Convert to Celsius for the test logic (assuming input is C)
        # Actually, let's store realistic C values to pass the check
        temp_c = np.clip(temp_data - 273.15, -50, 50) 
        hf.create_dataset('t2m', data=temp_c)

    yield path
    os.remove(path)

@pytest.fixture
def mock_hdf5_file_bad_time():
    """Create a file with inconsistent time steps."""
    fd, path = tempfile.mkstemp(suffix='.h5')
    os.close(fd)
    
    with h5py.File(path, 'w') as hf:
        # Irregular time steps
        time_data = np.array([0, 1, 3, 4, 8]) 
        hf.create_dataset('time', data=time_data)
        hf.create_dataset('latitude', data=[0.0])
        hf.create_dataset('longitude', data=[0.0])
        hf.create_dataset('t2m', data=[20.0])
    yield path
    os.remove(path)

@pytest.fixture
def mock_hdf5_file_bad_temp():
    """Create a file with impossible temperature."""
    fd, path = tempfile.mkstemp(suffix='.h5')
    os.close(fd)
    
    with h5py.File(path, 'w') as hf:
        hf.create_dataset('time', data=[0, 1])
        hf.create_dataset('latitude', data=[0.0])
        hf.create_dataset('longitude', data=[0.0])
        # 100 C is impossible for surface air
        hf.create_dataset('t2m', data=[100.0, 20.0])
    yield path
    os.remove(path)

def test_validate_temporal_resolution_pass(mock_hdf5_file):
    with h5py.File(mock_hdf5_file, 'r') as hf:
        assert validate_temporal_resolution(None, hf) is True

def test_validate_temporal_resolution_fail(mock_hdf5_file_bad_time):
    with h5py.File(mock_hdf5_file_bad_time, 'r') as hf:
        assert validate_temporal_resolution(None, hf) is False

def test_validate_grid_size_pass(mock_hdf5_file):
    with h5py.File(mock_hdf5_file, 'r') as hf:
        assert validate_grid_size(None, hf) is True

def test_validate_temperature_range_pass(mock_hdf5_file):
    with h5py.File(mock_hdf5_file, 'r') as hf:
        assert validate_temperature_range(None, hf) is True

def test_validate_temperature_range_fail(mock_hdf5_file_bad_temp):
    with h5py.File(mock_hdf5_file_bad_temp, 'r') as hf:
        assert validate_temperature_range(None, hf) is False