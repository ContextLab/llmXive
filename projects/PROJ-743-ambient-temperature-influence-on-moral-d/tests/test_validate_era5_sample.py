import pytest
import os
import h5py
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_era5_sample import validate_hdf5_sample
import logging

# Setup a mock logger for tests
logger = logging.getLogger("test_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

def create_mock_hdf5_file(path: Path, time_steps: int = 168, lat_steps: int = 4, lon_steps: int = 4):
    """Helper to create a mock ERA5-like HDF5 file."""
    with h5py.File(path, 'w') as f:
        # Create time dataset
        time_data = np.arange(time_steps) * 3600  # Hourly in seconds
        f.create_dataset('time', data=time_data)
        
        # Create lat/lon datasets with 0.25 resolution
        lats = np.linspace(51.0, 52.0, lat_steps) # ~0.33 deg diff, but we'll adjust for test
        lons = np.linspace(-1.0, 0.0, lon_steps)
        
        # Correct for 0.25 resolution for the test
        lats = np.arange(51.0, 52.0, 0.25)
        lons = np.arange(-1.0, 0.0, 0.25)
        
        f.create_dataset('latitude', data=lats)
        f.create_dataset('longitude', data=lons)
        
        # Create temperature data (2m temp in Kelvin, ~288K = 15C)
        temp_data = np.random.normal(288.0, 2.0, (time_steps, len(lats), len(lons)))
        f.create_dataset('t2m', data=temp_data)

def test_validate_hdf5_sample_success():
    """Test validation passes on a correctly formed file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file_path = tmp_path / "test_valid.h5"
        create_mock_hdf5_file(file_path)
        
        result = validate_hdf5_sample(file_path, logger)
        assert result is True

def test_validate_hdf5_sample_missing_file():
    """Test validation fails on non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "nonexistent.h5"
        result = validate_hdf5_sample(file_path, logger)
        assert result is False

def test_validate_hdf5_sample_wrong_resolution():
    """Test validation fails if temporal resolution is not hourly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file_path = tmp_path / "test_wrong_time.h5"
        
        # Create file with 2-hourly data (7200s)
        with h5py.File(file_path, 'w') as f:
            time_data = np.arange(84) * 7200  # 2 hours
            f.create_dataset('time', data=time_data)
            f.create_dataset('latitude', data=np.arange(51.0, 52.0, 0.25))
            f.create_dataset('longitude', data=np.arange(-1.0, 0.0, 0.25))
            temp_data = np.random.normal(288.0, 2.0, (84, 4, 4))
            f.create_dataset('t2m', data=temp_data)
        
        result = validate_hdf5_sample(file_path, logger)
        assert result is False

def test_validate_hdf5_sample_invalid_temp():
    """Test validation fails if temperature is out of physical range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file_path = tmp_path / "test_invalid_temp.h5"
        
        with h5py.File(file_path, 'w') as f:
            time_data = np.arange(168) * 3600
            f.create_dataset('time', data=time_data)
            f.create_dataset('latitude', data=np.arange(51.0, 52.0, 0.25))
            f.create_dataset('longitude', data=np.arange(-1.0, 0.0, 0.25))
            # Create impossible temperature (e.g., -200C = 73K, below min)
            temp_data = np.full((168, 4, 4), 100.0) 
            f.create_dataset('t2m', data=temp_data)
        
        result = validate_hdf5_sample(file_path, logger)
        assert result is False