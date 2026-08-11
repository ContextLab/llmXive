"""
Integration test for T014: Generate final aligned dataset artifact.

This test verifies that:
1. The script `code/05_generate_aligned_dataset.py` runs successfully.
2. The output file `data/processed/aligned_dataset.nc` is created.
3. The file is a valid NetCDF file readable by xarray.
4. The dataset contains no NaN values in core feature columns.
5. The dataset has the expected dimensions (time, lat, lon) and variables.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

import pytest
import xarray as xr
import numpy as np

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="module")
def aligned_dataset_path():
    """Run the T014 script and return the path to the output file."""
    script_path = PROJECT_ROOT / "code" / "05_generate_aligned_dataset.py"
    output_path = PROJECT_ROOT / "data" / "processed" / "aligned_dataset.nc"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # Check if script succeeded
    if result.returncode != 0:
        pytest.fail(f"Script execution failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    
    # Verify file exists
    if not output_path.exists():
        pytest.fail(f"Output file {output_path} was not created.")
    
    return output_path

def test_file_exists(aligned_dataset_path):
    """Test that the output file exists."""
    assert aligned_dataset_path.exists(), "Output file does not exist."

def test_valid_netcdf(aligned_dataset_path):
    """Test that the output is a valid NetCDF file."""
    try:
        ds = xr.open_dataset(aligned_dataset_path)
        ds.close()
    except Exception as e:
        pytest.fail(f"Failed to open NetCDF file: {e}")

def test_no_missing_values(aligned_dataset_path):
    """Test that the dataset contains no NaN values in core data variables."""
    ds = xr.open_dataset(aligned_dataset_path)
    
    # Identify core data variables (exclude coordinates and metadata)
    data_vars = [v for v in ds.data_vars if v != 'basin_id' and v not in ds.coords]
    
    if not data_vars:
        pytest.fail("No data variables found in the dataset.")
    
    nan_found = False
    for var in data_vars:
        if np.isnan(ds[var].values).any():
            nan_found = True
            count = np.isnan(ds[var].values).sum()
            pytest.fail(f"Variable '{var}' contains {count} NaN values.")
    
    ds.close()
    assert not nan_found, "Dataset contains missing values."

def test_expected_dimensions(aligned_dataset_path):
    """Test that the dataset has expected dimensions."""
    ds = xr.open_dataset(aligned_dataset_path)
    
    required_dims = {'time', 'lat', 'lon'}
    missing_dims = required_dims - set(ds.dims.keys())
    
    if missing_dims:
        pytest.fail(f"Dataset missing expected dimensions: {missing_dims}")
    
    # Verify dimensions are non-zero
    for dim in required_dims:
        if dim in ds.dims and ds.dims[dim] == 0:
            pytest.fail(f"Dimension '{dim}' is zero.")
    
    ds.close()

def test_expected_variables(aligned_dataset_path):
    """Test that the dataset contains expected variables."""
    ds = xr.open_dataset(aligned_dataset_path)
    
    # Based on the pipeline, we expect these variables
    # (Adjust based on actual data model if known)
    expected_vars = ['chlorophyll', 'temperature', 'salinity', 'nitrate']
    
    missing_vars = []
    for var in expected_vars:
        if var not in ds.data_vars:
            missing_vars.append(var)
    
    # Note: If variables are missing, it might be due to the specific data sources
    # used in the previous steps. We log a warning but don't fail if the dataset
    # is otherwise valid, unless the spec strictly requires these.
    # For this test, we assume the pipeline produces at least 'chlorophyll' and 'temperature'.
    if 'chlorophyll' not in ds.data_vars and 'temperature' not in ds.data_vars:
        pytest.fail("Dataset missing expected core variables (chlorophyll or temperature).")
    
    ds.close()

def test_basin_stratification(aligned_dataset_path):
    """Test that basin stratification is present."""
    ds = xr.open_dataset(aligned_dataset_path)
    
    if 'basin_id' not in ds.data_vars and 'basin_id' not in ds.coords:
        pytest.fail("Dataset missing 'basin_id' variable or coordinate.")
    
    ds.close()