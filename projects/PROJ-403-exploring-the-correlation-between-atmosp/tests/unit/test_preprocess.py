"""
Unit tests for data preprocessing utilities in src.data.preprocess.
"""
import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from pathlib import Path
from src.data.preprocess import (
    load_chunked_netcdf,
    slice_regional_domain,
    compute_monthly_climatology,
    compute_anomalies,
    detect_ar_events,
    aggregate_monthly_frequency,
    save_processed_dataset
)

@pytest.fixture
def sample_netcdf_file():
    """Create a temporary NetCDF file with sample data."""
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        time = np.arange("2020-01-01", "2020-12-31", dtype="datetime64[D]")
        lat = np.linspace(20, 60, 10)
        lon = np.linspace(100, 300, 10)
        
        data = np.random.rand(len(time), len(lat), len(lon))
        
        ds = xr.Dataset(
            {"ivt": (("time", "lat", "lon"), data)},
            coords={"time": time, "lat": lat, "lon": lon}
        )
        ds.to_netcdf(tmp.name)
        yield tmp.name
        os.unlink(tmp.name)

@pytest.fixture
def sample_z500_file():
    """Create a temporary NetCDF file with Z500 data."""
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        time = np.arange("2020-01-01", "2020-12-31", dtype="datetime64[D]")
        lat = np.linspace(20, 60, 10)
        lon = np.linspace(100, 300, 10)
        
        # Create data with some seasonal pattern for climatology testing
        time_days = np.arange(len(time))
        data = np.sin(2 * np.pi * time_days / 365) + np.random.rand(len(time), len(lat), len(lon)) * 0.1
        
        ds = xr.Dataset(
            {"z500": (("time", "lat", "lon"), data)},
            coords={"time": time, "lat": lat, "lon": lon}
        )
        ds.to_netcdf(tmp.name)
        yield tmp.name
        os.unlink(tmp.name)

@pytest.fixture
def sample_ar_data():
    """Create a temporary dataset with AR-like data."""
    time = np.arange("2020-01-01", "2020-01-10", dtype="datetime64[D]")
    lat = np.linspace(20, 60, 5)
    lon = np.linspace(100, 300, 5)
    
    # Create a block of high values
    data = np.zeros((len(time), len(lat), len(lon)))
    data[2:5, 2:4, 2:4] = 300.0  # Above threshold
    
    ds = xr.Dataset(
        {"ivt": (("time", "lat", "lon"), data)},
        coords={"time": time, "lat": lat, "lon": lon}
    )
    return ds

def test_load_chunked_netcdf(sample_netcdf_file):
    """Test loading a NetCDF file with Dask."""
    ds = load_chunked_netcdf(sample_netcdf_file, chunks={"time": 5})
    assert "ivt" in ds.data_vars
    assert isinstance(ds["ivt"].data, xr.core.dask.array.Array)
    assert ds.sizes["time"] == 366

def test_load_chunked_netcdf_nonexistent():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_chunked_netcdf("/nonexistent/path/file.nc")

def test_slice_regional_domain(sample_netcdf_file):
    """Test slicing the dataset to a regional domain."""
    ds = load_chunked_netcdf(sample_netcdf_file)
    sliced = slice_regional_domain(ds, lat_min=30, lat_max=50, lon_min=120, lon_max=280)
    assert sliced.sizes["lat"] < ds.sizes["lat"]
    assert sliced.sizes["lon"] < ds.sizes["lon"]
    assert sliced.sizes["lat"] > 0
    assert sliced.sizes["lon"] > 0

def test_compute_monthly_climatology(sample_z500_file):
    """Test computing monthly climatology."""
    ds = load_chunked_netcdf(sample_z500_file)
    clim = compute_monthly_climatology(ds, var_name="z500")
    assert clim.sizes["month"] == 12
    assert clim.sizes["lat"] == ds.sizes["lat"]
    assert clim.sizes["lon"] == ds.sizes["lon"]

def test_compute_anomalies(sample_z500_file):
    """Test computing anomalies (climatology subtraction)."""
    ds = load_chunked_netcdf(sample_z500_file)
    clim = compute_monthly_climatology(ds, var_name="z500")
    anom = compute_anomalies(ds, var_name="z500", climatology=clim)
    assert anom.sizes == ds["z500"].sizes
    # Anomalies should be centered around 0 (roughly)
    assert np.abs(anom.mean().values) < 1.0

def test_detect_ar_events(sample_ar_data):
    """Test AR event detection."""
    ds = sample_ar_data
    result = detect_ar_events(ds, var_name="ivt", threshold=250.0, min_duration=1)
    assert "ar_mask" in result.data_vars
    assert "ar_event_id" in result.data_vars
    # Check that the high values are detected
    assert result["ar_mask"].sum().values > 0

def test_aggregate_monthly_frequency(sample_ar_data):
    """Test monthly frequency aggregation."""
    # First detect events
    ds = sample_ar_data
    ar_ds = detect_ar_events(ds, var_name="ivt", threshold=250.0, min_duration=1)
    
    # Aggregate
    freq_ds = aggregate_monthly_frequency(ar_ds, event_id_var="ar_event_id")
    assert "ar_frequency" in freq_ds.data_vars
    # Since all data is in Jan, we expect 1 month
    assert freq_ds.sizes["time"] == 1

def test_save_processed_dataset(sample_ar_data):
    """Test saving a processed dataset."""
    ds = sample_ar_data
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.nc")
        save_processed_dataset(ds, output_path)
        assert os.path.exists(output_path)
        
        # Verify it can be loaded back
        loaded = xr.open_dataset(output_path)
        assert "ivt" in loaded.data_vars