"""
Tests for T001b: validate_era5.py
"""
import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import xarray as xr
import h5py
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from validate_era5 import (
    validate_hdf5_sample, 
    convert_netcdf_to_hdf5, 
    TEMPERATURE_MIN, 
    TEMPERATURE_MAX
)
from setup_logging import setup_logging

def create_mock_netcdf_file(tmp_path):
    """Create a mock netCDF file with expected structure for testing."""
    file_path = tmp_path / "mock_era5.nc"
    
    # Create time coordinates (7 days * 24 hours)
    times = np.arange(0, 7 * 24, 1) # hours
    # Convert to datetime objects for xarray
    import pandas as pd
    start_date = pd.Timestamp('2016-01-01')
    time_coords = pd.date_range(start=start_date, periods=len(times), freq='h')
    
    # Create data (in Kelvin, around 293K = 20C)
    lat = [51.4, 51.5, 51.6]
    lon = [-0.2, -0.1, 0.0]
    data = np.full((len(time_coords), len(lat), len(lon)), 293.15, dtype=np.float32)
    
    # Add some variation to test min/max
    data[0, 0, 0] = 223.15 # -50 C
    data[-1, -1, -1] = 333.15 # 60 C (edge case, should pass if inclusive)
    
    ds = xr.Dataset(
        data_vars={
            't2m': (['time', 'latitude', 'longitude'], data),
        },
        coords={
            'time': time_coords,
            'latitude': lat,
            'longitude': lon,
        }
    )
    
    ds.to_netcdf(file_path)
    return file_path

def test_validate_hdf5_sample_passes(tmp_path):
    """Test that a valid file passes validation."""
    nc_file = create_mock_netcdf_file(tmp_path)
    h5_file = tmp_path / "test_valid.h5"
    
    # Mock logger
    logger = setup_logging(None) # Dummy logger for test
    
    # Convert to HDF5
    # We need to mock the logger for convert function or pass a dummy
    class DummyLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    dummy_logger = DummyLogger()
    
    # Convert
    ds = xr.open_dataset(nc_file)
    convert_netcdf_to_hdf5(ds, h5_file, dummy_logger)
    ds.close()
    
    # Validate
    result = validate_hdf5_sample(h5_file, dummy_logger)
    assert result is True, "Valid file should pass validation"

def test_validate_hdf5_sample_fails_range(tmp_path):
    """Test that a file with out-of-range values fails."""
    file_path = tmp_path / "mock_bad_range.nc"
    
    import pandas as pd
    time_coords = pd.date_range(start='2016-01-01', periods=24, freq='h')
    lat = [51.5]
    lon = [-0.1]
    
    # Create data with a value > 60C (333.15K)
    data = np.full((24, len(lat), len(lon)), 340.0, dtype=np.float32) # 66.85 C
    
    ds = xr.Dataset(
        data_vars={'t2m': (['time', 'latitude', 'longitude'], data)},
        coords={'time': time_coords, 'latitude': lat, 'longitude': lon}
    )
    ds.to_netcdf(file_path)
    
    h5_file = tmp_path / "test_bad_range.h5"
    ds.to_netcdf(h5_file, engine='netcdf4')
    ds.close()
    
    class DummyLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    dummy_logger = DummyLogger()
    
    result = validate_hdf5_sample(h5_file, dummy_logger)
    assert result is False, "File with out-of-range temperature should fail"

def test_validate_hdf5_sample_fails_resolution(tmp_path):
    """Test that a file with wrong resolution fails."""
    file_path = tmp_path / "mock_bad_res.nc"
    
    import pandas as pd
    # Only 2 time points (12 hours apart? No, just 2 points)
    # To fail resolution, we need non-hourly steps.
    # Let's create 2 points 2 hours apart.
    time_coords = pd.date_range(start='2016-01-01', periods=2, freq='2h')
    lat = [51.5]
    lon = [-0.1]
    data = np.full((2, len(lat), len(lon)), 293.15, dtype=np.float32)
    
    ds = xr.Dataset(
        data_vars={'t2m': (['time', 'latitude', 'longitude'], data)},
        coords={'time': time_coords, 'latitude': lat, 'longitude': lon}
    )
    ds.to_netcdf(file_path)
    
    h5_file = tmp_path / "test_bad_res.h5"
    ds.to_netcdf(h5_file, engine='netcdf4')
    ds.close()
    
    class DummyLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    dummy_logger = DummyLogger()
    
    result = validate_hdf5_sample(h5_file, dummy_logger)
    assert result is False, "File with non-hourly resolution should fail"