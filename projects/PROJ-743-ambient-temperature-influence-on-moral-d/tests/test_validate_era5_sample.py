import os
import pytest
import h5py
import numpy as np
from pathlib import Path
from datetime import datetime

# Import the function to test
from code.validate_era5_sample import validate_era5_sample

@pytest.fixture
def mock_h5_file(tmp_path):
    """Create a mock HDF5 file that mimics the expected ERA5 sample structure."""
    file_path = tmp_path / "era_sample.h5"
    
    # Create file with expected structure
    with h5py.File(file_path, 'w') as f:
        # Create time, lat, lon coordinates
        # Jan 1 to Jan 7 = 168 hours
        f.create_dataset('time', data=np.arange(168))
        # 0.25 deg grid
        lats = np.arange(50.0, 53.0, 0.25)
        lons = np.arange(-2.0, 2.0, 0.25)
        f.create_dataset('lat', data=lats)
        f.create_dataset('lon', data=lons)
        
        # Create t2m data: shape (168, len(lats), len(lons))
        # Values in Kelvin, plausible range 270-300
        data = np.random.uniform(273.15, 293.15, (168, len(lats), len(lons)))
        f.create_dataset('t2m', data=data)
        
    return str(file_path)

def test_validate_era5_sample_pass(mock_h5_file):
    """Test that a valid file returns PASS."""
    result = validate_era5_sample(mock_h5_file)
    
    assert result["status"] == "PASS"
    assert result["temporal_resolution_ok"] is True
    assert result["grid_size_ok"] is True
    assert result["temperature_values_valid"] is True
    assert "Validation PASSED" in str(result["details"]) or "valid" in str(result["details"]).lower()

def test_validate_era5_sample_missing_file(tmp_path):
    """Test that a missing file returns FAIL."""
    result = validate_era5_sample(str(tmp_path / "nonexistent.h5"))
    
    assert result["status"] == "FAIL"
    assert "File not found" in str(result["details"])

def test_validate_era5_sample_wrong_temporal_resolution(mock_h5_file, tmp_path):
    """Test detection of wrong temporal resolution (e.g., daily instead of hourly)."""
    # Modify the mock file to have only 7 time steps
    file_path = tmp_path / "era_sample_daily.h5"
    with h5py.File(file_path, 'w') as f:
        f.create_dataset('time', data=np.arange(7))
        lats = np.arange(50.0, 53.0, 0.25)
        lons = np.arange(-2.0, 2.0, 0.25)
        f.create_dataset('lat', data=lats)
        f.create_dataset('lon', data=lons)
        data = np.random.uniform(273.15, 293.15, (7, len(lats), len(lons)))
        f.create_dataset('t2m', data=data)
    
    result = validate_era5_sample(str(file_path))
    
    assert result["status"] == "FAIL"
    assert result["temporal_resolution_ok"] is False
    assert "Unexpected time steps" in str(result["details"])

def test_validate_era5_sample_wrong_grid_size(mock_h5_file, tmp_path):
    """Test detection of wrong grid size (e.g., 0.5 deg)."""
    file_path = tmp_path / "era_sample_coarse.h5"
    with h5py.File(file_path, 'w') as f:
        f.create_dataset('time', data=np.arange(168))
        # 0.5 deg grid
        lats = np.arange(50.0, 53.0, 0.5)
        lons = np.arange(-2.0, 2.0, 0.5)
        f.create_dataset('lat', data=lats)
        f.create_dataset('lon', data=lons)
        data = np.random.uniform(273.15, 293.15, (168, len(lats), len(lons)))
        f.create_dataset('t2m', data=data)
    
    result = validate_era5_sample(str(file_path))
    
    assert result["status"] == "FAIL"
    assert result["grid_size_ok"] is False
    assert "grid size mismatch" in str(result["details"]).lower()

def test_validate_era5_sample_invalid_temp(mock_h5_file, tmp_path):
    """Test detection of invalid temperature values."""
    file_path = tmp_path / "era_sample_bad_temp.h5"
    with h5py.File(file_path, 'w') as f:
        f.create_dataset('time', data=np.arange(168))
        lats = np.arange(50.0, 53.0, 0.25)
        lons = np.arange(-2.0, 2.0, 0.25)
        f.create_dataset('lat', data=lats)
        f.create_dataset('lon', data=lons)
        # Values outside plausible range (e.g., 100K or 400K)
        data = np.random.uniform(100.0, 150.0, (168, len(lats), len(lons)))
        f.create_dataset('t2m', data=data)
    
    result = validate_era5_sample(str(file_path))
    
    assert result["status"] == "FAIL"
    assert result["temperature_values_valid"] is False
    assert "Temperature range invalid" in str(result["details"])