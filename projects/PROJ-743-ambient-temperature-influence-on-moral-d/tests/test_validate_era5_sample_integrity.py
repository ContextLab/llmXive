import os
import tempfile
import pytest
import h5py
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_era5_sample_integrity import (
    validate_temporal_resolution,
    validate_grid_size,
    validate_temperature_range
)

@pytest.fixture
def temp_h5_file():
    """Create a temporary valid HDF5 file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        path = tmp.name
    
    with h5py.File(path, 'w') as f:
        # Create time dimension (hourly)
        time_data = np.arange(0, 86400 * 3, 3600) # 3 days of hourly data
        f.create_dataset('time', data=time_data)
        
        # Create spatial dimensions
        f.create_dataset('lat', data=np.linspace(50, 52, 10))
        f.create_dataset('lon', data=np.linspace(-1, 1, 10))
        
        # Create temperature data (valid range)
        temp_data = np.random.uniform(270, 300, (len(time_data), 10, 10)) # Kelvin-ish, but let's pretend it's C for test or adjust
        # Actually, let's make it realistic C for the validator check
        temp_data = np.random.uniform(10, 30, (len(time_data), 10, 10)) 
        f.create_dataset('t2m', data=temp_data)
    
    yield path
    os.unlink(path)

@pytest.fixture
def temp_h5_file_bad_time():
    """Create a temporary HDF5 file with bad time resolution."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        path = tmp.name
    
    with h5py.File(path, 'w') as f:
        # Create time dimension (10 minutes resolution)
        time_data = np.arange(0, 600, 600) 
        f.create_dataset('time', data=time_data)
        f.create_dataset('lat', data=np.linspace(50, 52, 10))
        f.create_dataset('t2m', data=np.random.rand(1, 10, 10))
    
    yield path
    os.unlink(path)

@pytest.fixture
def temp_h5_file_bad_temp():
    """Create a temporary HDF5 file with out-of-range temperature."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        path = tmp.name
    
    with h5py.File(path, 'w') as f:
        time_data = np.arange(0, 3600, 3600)
        f.create_dataset('time', data=time_data)
        f.create_dataset('lat', data=np.linspace(50, 52, 10))
        # Temp = -100 C (invalid)
        f.create_dataset('t2m', data=np.array([-100.0]))
    
    yield path
    os.unlink(path)

def test_validate_temporal_resolution_valid(temp_h5_file):
    is_valid, msg = validate_temporal_resolution(None, temp_h5_file)
    assert is_valid is True
    assert "Temporal resolution validated" in msg

def test_validate_temporal_resolution_invalid(temp_h5_file_bad_time):
    is_valid, msg = validate_temporal_resolution(None, temp_h5_file_bad_time)
    assert is_valid is False
    assert "mismatch" in msg

def test_validate_grid_size_valid(temp_h5_file):
    is_valid, msg = validate_grid_size(None, temp_h5_file)
    assert is_valid is True
    assert "Spatial dimensions validated" in msg

def test_validate_temperature_range_valid(temp_h5_file):
    is_valid, msg = validate_temperature_range(None, temp_h5_file)
    assert is_valid is True
    assert "Temperature range validated" in msg

def test_validate_temperature_range_invalid(temp_h5_file_bad_temp):
    is_valid, msg = validate_temperature_range(None, temp_h5_file_bad_temp)
    assert is_valid is False
    assert "out of range" in msg