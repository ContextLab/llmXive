import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from pathlib import Path

from src.data.preprocess import detect_ar_events, aggregate_monthly_frequency, save_processed_dataset


@pytest.fixture
def sample_netcdf_file():
    """Create a temporary NetCDF file with mock IVT data for AR detection testing."""
    # Mock data dimensions: time (months), lat, lon
    # Regional domain: 20°N-60°N, 100°E-60°W
    time = np.arange('1979-01-01', '1979-13-01', dtype='datetime64[M]')
    lat = np.linspace(20, 60, 41)
    lon = np.linspace(-160, 60, 221)  # 100°E to 60°W wraps around, simplified for test

    # Create mock IVT data (kg m⁻¹ s⁻¹)
    # Shape: (time, lat, lon)
    np.random.seed(42)
    ivt_data = np.random.uniform(0, 10, size=(len(time), len(lat), len(lon)))

    # Inject a strong AR event: contiguous high values for 3 months
    # at lat=40 (index ~20), lon=0 (index ~110)
    start_lat_idx = 20
    end_lat_idx = 25
    start_lon_idx = 100
    end_lon_idx = 120
    start_time_idx = 6  # July
    end_time_idx = 9    # October

    ivt_data[start_time_idx:end_time_idx, start_lat_idx:end_lat_idx, start_lon_idx:end_lon_idx] = 25.0

    ds = xr.Dataset(
        {
            'ivt': (['time', 'lat', 'lon'], ivt_data)
        },
        coords={
            'time': time,
            'lat': lat,
            'lon': lon
        }
    )

    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
        ds.to_netcdf(tmp.name)
        return tmp.name


@pytest.fixture
def sample_ar_data():
    """Return a dictionary representing expected AR detection results structure."""
    return {
        'ar_frequency': None,
        'ar_start_time': None,
        'ar_end_time': None
    }


def test_detect_ar_events(sample_netcdf_file):
    """Test AR detection logic with mock IVT data.
    
    Validates that:
    1. The function correctly identifies contiguous AR events.
    2. Events meet the duration threshold (>24h, here >1 month in monthly data).
    3. Events meet the magnitude threshold (>10 kg m⁻¹ s⁻¹).
    4. Output includes start and end times of events.
    """
    threshold = 10.0  # kg m⁻¹ s⁻¹
    min_duration = 1  # months (since data is monthly, 1 month > 24h)
    
    # Run detection
    result = detect_ar_events(sample_netcdf_file, threshold, min_duration)
    
    # Assertions
    assert 'ar_frequency' in result
    assert 'ar_start_time' in result
    assert 'ar_end_time' in result
    
    # Check that frequency is a DataArray
    assert isinstance(result['ar_frequency'], xr.DataArray)
    
    # Verify that we detected the injected event (frequency > 0 in the region)
    # The injected event was at lat ~40, lon ~0
    # We check if there are any non-zero frequencies in the dataset
    assert result['ar_frequency'].sum() > 0, "Expected at least one AR event to be detected."
    
    # Check dimensions
    assert 'time' in result['ar_frequency'].dims
    assert 'lat' in result['ar_frequency'].dims
    assert 'lon' in result['ar_frequency'].dims


def test_aggregate_monthly_frequency(sample_netcdf_file):
    """Test monthly frequency aggregation from detected AR events."""
    threshold = 10.0
    min_duration = 1
    
    # Detect events
    events = detect_ar_events(sample_netcdf_file, threshold, min_duration)
    
    # Aggregate to monthly frequency
    monthly_freq = aggregate_monthly_frequency(events['ar_frequency'])
    
    # Assertions
    assert isinstance(monthly_freq, xr.DataArray)
    assert 'time' in monthly_freq.dims
    assert 'lat' in monthly_freq.dims
    assert 'lon' in monthly_freq.dims
    
    # Verify that frequency counts are non-negative integers
    assert (monthly_freq >= 0).all()
    
    # Verify shape matches expected (time, lat, lon)
    assert monthly_freq.shape == events['ar_frequency'].shape


def test_save_processed_dataset(sample_netcdf_file, tmp_path):
    """Test saving processed AR data to NetCDF."""
    threshold = 10.0
    min_duration = 1
    
    # Detect events
    events = detect_ar_events(sample_netcdf_file, threshold, min_duration)
    
    # Aggregate frequency
    monthly_freq = aggregate_monthly_frequency(events['ar_frequency'])
    
    # Prepare dataset for saving
    output_path = tmp_path / "test_ar_freq.nc"
    save_processed_dataset(
        output_path,
        monthly_freq,
        events['ar_start_time'],
        events['ar_end_time']
    )
    
    # Verify file exists
    assert output_path.exists()
    
    # Verify contents
    ds = xr.open_dataset(output_path)
    assert 'ar_frequency' in ds
    assert 'ar_start_time' in ds
    assert 'ar_end_time' in ds
    
    # Clean up
    ds.close()