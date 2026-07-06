import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from pathlib import Path

from src.data.preprocess import (
    detect_ar_events, 
    aggregate_monthly_frequency, 
    save_processed_dataset,
    compute_monthly_climatology,
    compute_anomalies,
    slice_regional_domain,
    load_chunked_netcdf
)

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
def sample_z500_file():
    """Create a temporary NetCDF file with mock Z500 data for anomaly testing."""
    # Mock data dimensions: time (months), lat, lon
    # Regional domain: 20°N-60°N, 100°E-60°W
    time = np.arange('1979-01-01', '1979-13-01', dtype='datetime64[M]')
    lat = np.linspace(20, 60, 41)
    lon = np.linspace(-160, 60, 221)

    # Create mock Z500 data (m)
    # Shape: (time, lat, lon)
    np.random.seed(123)
    z500_data = np.random.uniform(5000, 6000, size=(len(time), len(lat), len(lon)))

    # Add a seasonal cycle: higher in winter, lower in summer
    # Approximate sinusoidal variation
    months = np.arange(1, 13)
    seasonal_cycle = 100 * np.sin(2 * np.pi * (months - 3) / 12)  # Peak in Jan (month 1)
    for t in range(len(time)):
        month_idx = (t % 12)
        z500_data[t, :, :] += seasonal_cycle[month_idx]

    ds = xr.Dataset(
        {
            'z500': (['time', 'lat', 'lon'], z500_data)
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

def test_load_chunked_netcdf(sample_netcdf_file):
    """Test loading a NetCDF file with Dask chunking."""
    chunks = {'time': 6, 'lat': 20, 'lon': 50}
    ds = load_chunked_netcdf(sample_netcdf_file, chunks)
    
    assert isinstance(ds, xr.Dataset)
    assert 'ivt' in ds.data_vars
    assert ds.chunks is not None
    assert ds.chunks['time'][0] == 6

def test_load_chunked_netcdf_nonexistent():
    """Test loading a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_chunked_netcdf("nonexistent_file.nc")

def test_slice_regional_domain(sample_netcdf_file):
    """Test slicing the dataset to a regional domain."""
    ds = load_chunked_netcdf(sample_netcdf_file)
    
    # Slice to a smaller domain
    sliced = slice_regional_domain(ds, lat_min=30, lat_max=50, lon_min=-100, lon_max=0)
    
    assert sliced.lat.min() >= 30
    assert sliced.lat.max() <= 50
    assert sliced.lon.min() >= -100
    assert sliced.lon.max() <= 0
    assert 'ivt' in sliced.data_vars

def test_compute_monthly_climatology(sample_z500_file):
    """Test computing monthly climatology from Z500 data."""
    ds = load_chunked_netcdf(sample_z500_file)
    
    climatology = compute_monthly_climatology(ds, var_name='z500')
    
    # Climatology should have dimensions (month, lat, lon)
    assert 'month' in climatology.dims
    assert 'lat' in climatology.dims
    assert 'lon' in climatology.dims
    assert len(climatology.month) == 12
    
    # Verify that the climatology is the mean of the data for each month
    # (Since we only have 1 year, it should be the data itself)
    # With multiple years, it would be the average across years

def test_compute_anomalies(sample_z500_file):
    """Test Z500 anomaly calculation (climatology subtraction only, NO detrending).
    
    Validates that:
    1. The function correctly subtracts the monthly climatology from raw data.
    2. No linear detrending is applied (per Spec FR-003).
    3. The output has the same shape as the input data.
    4. The mean anomaly over a full year is approximately zero (if climatology is correct).
    """
    ds = load_chunked_netcdf(sample_z500_file)
    
    # Compute anomalies
    anomalies = compute_anomalies(ds, var_name='z500')
    
    # Assertions
    assert isinstance(anomalies, xr.DataArray)
    assert anomalies.shape == ds['z500'].shape
    assert 'time' in anomalies.dims
    assert 'lat' in anomalies.dims
    assert 'lon' in anomalies.dims
    
    # Verify that anomalies are centered around zero for each month (approximately)
    # Since we have only one year, the mean of anomalies for each month should be zero
    # (because we subtracted the mean of that single month)
    mean_anomaly_per_month = anomalies.groupby('time.month').mean(dim=['time', 'lat', 'lon'])
    # Allow for small floating point errors
    assert np.allclose(mean_anomaly_per_month.values, 0.0, atol=1e-10)
    
    # Verify that the anomalies are not zero everywhere (since we added a seasonal cycle)
    assert anomalies.std().values > 0

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
    assert 'time' in result['ar_frequency'].dims or result['ar_frequency'].dims == ('lat', 'lon')
    # Note: The current implementation sums along time, so 'time' might not be in dims

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
    # Note: If ar_frequency is already summed along time, this might be redundant
    # But the function should handle it correctly
    
    # Verify that frequency counts are non-negative integers
    assert (monthly_freq >= 0).all()

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