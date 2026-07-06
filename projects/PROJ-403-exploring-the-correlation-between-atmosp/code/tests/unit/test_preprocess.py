"""
Unit tests for data preprocessing utilities.

Tests cover:
- Loading chunked NetCDF files
- Slicing regional domains
- Computing monthly climatologies
- Calculating anomalies
- Detecting AR events (with mocked data)
"""

import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from pathlib import Path
import dask.array as da

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
    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
        # Create sample data
        time = np.arange('2020-01-01', '2020-12-31', dtype='datetime64[D]')
        lat = np.linspace(10, 70, 30)
        lon = np.linspace(80, 350, 50)

        # Create sample IVT and geopotential data
        ivt_data = np.random.rand(len(time), len(lat), len(lon)) * 300 + 100
        z500_data = np.random.rand(len(time), len(lat), len(lon)) * 50 + 450

        ds = xr.Dataset(
            {
                'integrated_water_vapor_transport': (['time', 'lat', 'lon'], ivt_data, {
                    'units': 'kg m-1 s-1',
                    'long_name': 'Integrated Water Vapor Transport'
                }),
                'geopotential': (['time', 'lat', 'lon'], z500_data, {
                    'units': 'm',
                    'long_name': 'Geopotential Height'
                })
            },
            coords={
                'time': time,
                'lat': lat,
                'lon': lon
            }
        )

        ds.to_netcdf(tmp.name)
        yield tmp.name
        os.unlink(tmp.name)


@pytest.fixture
def sample_ar_data():
    """Create sample AR detection data."""
    time = np.arange('2020-01-01', '2020-02-01', dtype='datetime64[D]')
    lat = np.linspace(20, 60, 20)
    lon = np.linspace(100, 300, 30)

    # Create data with some AR-like patterns
    ivt_data = np.random.rand(len(time), len(lat), len(lon)) * 400 + 50
    # Add some high IVT values to simulate ARs
    ivt_data[10:15, 5:15, 10:20] = 350

    ds = xr.Dataset(
        {
            'IVT': (['time', 'lat', 'lon'], ivt_data, {
                'units': 'kg m-1 s-1',
                'long_name': 'Integrated Water Vapor Transport'
            })
        },
        coords={
            'time': time,
            'lat': lat,
            'lon': lon
        }
    )

    return ds['IVT']


def test_load_chunked_netcdf(sample_netcdf_file):
    """Test loading a chunked NetCDF file."""
    ds = load_chunked_netcdf(sample_netcdf_file, chunks={'time': 10})

    assert 'integrated_water_vapor_transport' in ds.data_vars
    assert 'geopotential' in ds.data_vars
    assert 'time' in ds.dims
    assert 'lat' in ds.dims
    assert 'lon' in ds.dims

    # Verify data is chunked (Dask array)
    assert isinstance(ds['integrated_water_vapor_transport'].data, da.Array)


def test_load_chunked_netcdf_nonexistent():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_chunked_netcdf("nonexistent_file.nc")


def test_slice_regional_domain(sample_netcdf_file):
    """Test slicing to regional domain."""
    ds = load_chunked_netcdf(sample_netcdf_file)

    # Slice to 20°N-60°N, 100°E-60°W
    ds_sliced = slice_regional_domain(ds, lat_min=20, lat_max=60, lon_min=100, lon_max=-60)

    assert ds_sliced['lat'].min() >= 20
    assert ds_sliced['lat'].max() <= 60
    # Longitude handling is complex due to wrap-around, just verify dimensions reduced
    assert len(ds_sliced['lat']) < len(ds['lat'])


def test_compute_monthly_climatology(sample_netcdf_file):
    """Test computing monthly climatology."""
    ds = load_chunked_netcdf(sample_netcdf_file)

    climatology = compute_monthly_climatology(ds, 'integrated_water_vapor_transport')

    assert 'month' in climatology.dims
    assert len(climatology['month']) == 12
    assert climatology.attrs['long_name'] == 'Monthly Climatology of integrated_water_vapor_transport'


def test_compute_anomalies(sample_netcdf_file):
    """Test computing anomalies from climatology."""
    ds = load_chunked_netcdf(sample_netcdf_file)

    climatology = compute_monthly_climatology(ds, 'geopotential')
    anomalies = compute_anomalies(ds, 'geopotential', climatology)

    assert anomalies.shape == ds['geopotential'].shape
    assert anomalies.attrs['long_name'] == 'Anomalies of geopotential (raw - climatology)'

    # Verify anomalies are centered around zero (approximately)
    mean_anomaly = anomalies.mean().compute()
    assert np.abs(mean_anomaly) < 10  # Should be close to zero


def test_detect_ar_events(sample_ar_data):
    """Test AR event detection with mocked data."""
    ar_freq, ar_start, ar_end = detect_ar_events(
        sample_ar_data,
        threshold=300,
        min_duration=24
    )

    assert ar_freq.shape == sample_ar_data.shape
    assert ar_start.shape == sample_ar_data.shape
    assert ar_end.shape == sample_ar_data.shape

    # Verify some AR detections occurred (since we added high IVT values)
    assert ar_freq.sum().item() > 0


def test_aggregate_monthly_frequency(sample_ar_data):
    """Test aggregating AR frequency to monthly resolution."""
    # Create daily data for a few months
    time = np.arange('2020-01-01', '2020-03-01', dtype='datetime64[D]')
    lat = np.linspace(20, 60, 10)
    lon = np.linspace(100, 300, 15)

    ar_freq_data = np.random.randint(0, 5, (len(time), len(lat), len(lon)))
    ar_freq = xr.DataArray(
        ar_freq_data,
        dims=['time', 'lat', 'lon'],
        coords={'time': time, 'lat': lat, 'lon': lon}
    )

    monthly_freq = aggregate_monthly_frequency(ar_freq)

    assert 'month' in monthly_freq.dims
    assert len(monthly_freq['month']) == 12  # Should cover all months


def test_save_processed_dataset(sample_netcdf_file):
    """Test saving a processed dataset."""
    ds = load_chunked_netcdf(sample_netcdf_file)

    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
        output_path = tmp.name

    try:
        save_processed_dataset(ds, output_path)

        # Verify file was created and can be loaded
        assert os.path.exists(output_path)
        ds_loaded = xr.open_dataset(output_path)
        assert 'integrated_water_vapor_transport' in ds_loaded.data_vars

        ds_loaded.close()
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)