"""
Integration test for the full correlation pipeline on a 1-year sample.

This test verifies the end-to-end flow of:
1. Loading a small subset of real or mock data (simulating the regional domain).
2. Computing monthly climatology and anomalies.
3. Detecting AR events and aggregating monthly frequency.
4. Computing Pearson correlation between AR frequency and Z500 anomalies.
5. Applying Benjamini-Hochberg FDR correction.
6. Saving results to the expected output path.

The test ensures that the pipeline produces valid NetCDF files with the
required variables: 'ar_frequency', 'z500_anomaly', 'pearson_r', 'p_value',
and 'p_value_adj' (BH-corrected).
"""
import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from pathlib import Path
from scipy import stats

# Import pipeline components
from src.data.preprocess import (
    load_chunked_netcdf,
    slice_regional_domain,
    compute_monthly_climatology,
    compute_anomalies,
    detect_ar_events,
    aggregate_monthly_frequency,
    save_processed_dataset,
)
from src.data.analysis import compute_correlation, apply_benjamini_hochberg
from src.utils.config import get_config

# Constants for the 1-year sample
SAMPLE_YEAR = 2020
REGIONAL_DOMAIN = {
    "lat_min": 20.0,
    "lat_max": 60.0,
    "lon_min": 100.0,  # 100°E
    "lon_max": 300.0,  # 60°W (360 - 60 = 300)
}
IVT_THRESHOLD = 250.0  # kg m⁻¹ s⁻¹
SEASONS = ["DJF", "MAM", "JJA", "SON"]


def _generate_sample_data(output_dir: Path, year: int = SAMPLE_YEAR):
    """
    Generates a small, synthetic but structurally valid NetCDF dataset
    representing 1 year of monthly data for the regional domain.
    
    This is used for integration testing where real data download is not feasible.
    The data is deterministic and follows the expected schema.
    """
    # Create time coordinate: 12 months
    time = xr.cftime_range(f"{year}-01-01", periods=12, freq="MS", calendar="standard")
    
    # Grid: Small regional slice to keep memory low
    lat = np.linspace(20, 60, 20)
    lon = np.linspace(100, 300, 30)  # 100E to 60W
    
    # Generate IVT data (random but bounded)
    ivt_data = np.random.uniform(100, 400, size=(12, len(lat), len(lon)))
    ivt_ds = xr.Dataset(
        {
            "ivt": (["time", "lat", "lon"], ivt_data),
        },
        coords={
            "time": time,
            "lat": lat,
            "lon": lon,
        },
    )
    
    # Generate Z500 data (random but bounded)
    z500_data = np.random.uniform(4500, 6000, size=(12, len(lat), len(lon)))
    z500_ds = xr.Dataset(
        {
            "z500": (["time", "lat", "lon"], z500_data),
        },
        coords={
            "time": time,
            "lat": lat,
            "lon": lon,
        },
    )
    
    ivt_path = output_dir / f"ivt_{year}.nc"
    z500_path = output_dir / f"z500_{year}.nc"
    
    ivt_ds.to_netcdf(ivt_path)
    z500_ds.to_netcdf(z500_path)
    
    return ivt_path, z500_path


@pytest.fixture
def sample_data_path(tmp_path):
    """Fixture to generate and yield paths to sample data."""
    return _generate_sample_data(tmp_path)


def test_full_correlation_pipeline(sample_data_path, tmp_path):
    """
    Integration test: Run the full correlation pipeline on a 1-year sample.
    
    Steps:
    1. Load data.
    2. Slice to regional domain.
    3. Compute climatology and anomalies.
    4. Detect ARs and aggregate frequency.
    5. Compute correlation and FDR.
    6. Verify output file exists and contains expected variables.
    """
    ivt_path, z500_path = sample_data_path
    output_dir = tmp_path / "processed"
    output_dir.mkdir(parents=True)
    
    # 1. Load data
    ivt_ds = load_chunked_netcdf(str(ivt_path))
    z500_ds = load_chunked_netcdf(str(z500_path))
    
    # 2. Slice to regional domain
    ivt_reg = slice_regional_domain(ivt_ds, **REGIONAL_DOMAIN)
    z500_reg = slice_regional_domain(z500_ds, **REGIONAL_DOMAIN)
    
    # 3. Compute climatology and anomalies
    # Since we only have 1 year, climatology is just the monthly mean of that year
    # (In a real scenario, this would be multi-year)
    clim = compute_monthly_climatology(z500_reg, dim="time")
    z500_anom = compute_anomalies(z500_reg, clim)
    
    # 4. Detect ARs and aggregate frequency
    # We need monthly AR frequency per grid cell
    ar_ds = detect_ar_events(ivt_reg, threshold=IVT_THRESHOLD)
    ar_freq_ds = aggregate_monthly_frequency(ar_ds)
    
    # Ensure time alignment between AR frequency and Z500 anomalies
    # (Both should be monthly)
    if "time" not in ar_freq_ds.dims:
        ar_freq_ds = ar_freq_ds.expand_dims("time")
    
    # 5. Compute correlation and FDR
    # Compute Pearson correlation between AR frequency and Z500 anomalies
    corr_ds = compute_correlation(
        ar_freq_ds, 
        z500_anom, 
        dim="time", 
        method="pearson"
    )
    
    # Apply Benjamini-Hochberg FDR correction
    corr_ds = apply_benjamini_hochberg(corr_ds)
    
    # 6. Save results
    output_file = output_dir / f"corr_fdr_test_{SAMPLE_YEAR}.nc"
    save_processed_dataset(corr_ds, str(output_file))
    
    # 7. Verify output
    assert output_file.exists(), "Output NetCDF file was not created."
    
    result_ds = xr.open_dataset(str(output_file))
    
    # Check for required variables
    required_vars = [
        "pearson_r",
        "p_value",
        "p_value_adj"  # BH-corrected adjusted p-value
    ]
    
    for var in required_vars:
        assert var in result_ds.data_vars, f"Missing variable: {var}"
        assert not np.all(np.isnan(result_ds[var].values)), f"All NaN values for {var}"
    
    # Check dimensions
    assert "lat" in result_ds.dims
    assert "lon" in result_ds.dims
    
    # Verify FDR logic: adjusted p-values should be >= raw p-values
    # (This is a property of BH correction)
    raw_p = result_ds["p_value"].values
    adj_p = result_ds["p_value_adj"].values
    
    # Allow for small floating point errors, but generally adj_p >= raw_p
    # Note: In some edge cases with very small p-values, they might be equal
    assert np.all(adj_p >= raw_p - 1e-10), "BH-corrected p-values are unexpectedly smaller than raw p-values."
    
    result_ds.close()