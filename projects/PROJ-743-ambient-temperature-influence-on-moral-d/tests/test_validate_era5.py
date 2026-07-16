"""
Tests for code/validate_era5_sample.py
"""
import pytest
import os
import tempfile
import h5py
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from validate_era5_sample import validate_era5_sample, FR_014_GRID_SIZE_DEG, FR_014_TEMPORAL_RESOLUTION_HOURS

def create_mock_era5_file(path, time_step_hours=1, lat_spacing=0.25, lon_spacing=0.25, valid=True):
    """Helper to create a mock H5 file mimicking ERA5 structure."""
    with h5py.File(path, 'w') as f:
        # Create time array
        # Start at 0, step by time_step_hours * 3600 seconds
        num_times = 10
        times = np.arange(num_times) * (time_step_hours * 3600)
        f.create_dataset('time', data=times)
        
        # Create lat/lon arrays
        num_lats = 20
        num_lons = 20
        lats = np.arange(num_lats) * lat_spacing
        lons = np.arange(num_lons) * lon_spacing
        
        f.create_dataset('latitude', data=lats)
        f.create_dataset('longitude', data=lons)
        
        # Create dummy temperature data
        temp_data = np.random.rand(num_times, num_lats, num_lons)
        f.create_dataset('temperature_2m', data=temp_data)

def test_valid_hourly_resolution():
    """Test that a file with 1-hour steps passes."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        create_mock_era5_file(tmp_path, time_step_hours=1)
        assert validate_era5_sample(tmp_path) is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_invalid_temporal_resolution():
    """Test that a file with 2-hour steps fails."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        create_mock_era5_file(tmp_path, time_step_hours=2)
        assert validate_era5_sample(tmp_path) is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_invalid_lat_grid():
    """Test that a file with wrong lat spacing fails."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        create_mock_era5_file(tmp_path, lat_spacing=0.5)
        assert validate_era5_sample(tmp_path) is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_invalid_lon_grid():
    """Test that a file with wrong lon spacing fails."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        create_mock_era5_file(tmp_path, lon_spacing=0.5)
        assert validate_era5_sample(tmp_path) is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_missing_file():
    """Test that a non-existent file returns False."""
    assert validate_era5_sample("/nonexistent/path/file.h5") is False

def test_missing_keys():
    """Test that a file missing required keys fails."""
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with h5py.File(tmp_path, 'w') as f:
            f.create_dataset('temperature_2m', data=np.random.rand(10, 10, 10))
            # Missing time, lat, lon
        assert validate_era5_sample(tmp_path) is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
