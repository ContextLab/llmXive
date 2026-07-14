"""
Integration test for MODIS data fetching task (T011b).

This test verifies that:
1. The fetch script runs without errors
2. The output file is created
3. The output file is a valid NetCDF file
4. The file contains expected variables
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest
import xarray as xr
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.mark.integration
def test_modis_fetch_creates_file():
    """Test that the fetch script creates the output file."""
    output_path = project_root / "data" / "raw" / "modis.nc"
    
    # Remove existing file if present
    if output_path.exists():
        output_path.unlink()
    
    # Run the fetch script
    script_path = project_root / "code" / "01_fetch_modis.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    # Assert script ran successfully
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Assert file was created
    assert output_path.exists(), "Output file was not created"
    
    # Assert file is not empty
    assert output_path.stat().st_size > 0, "Output file is empty"

@pytest.mark.integration
def test_modis_fetch_valid_netcdf():
    """Test that the output file is a valid NetCDF file."""
    output_path = project_root / "data" / "raw" / "modis.nc"
    
    # Ensure file exists (run fetch if needed)
    if not output_path.exists():
        script_path = project_root / "code" / "01_fetch_modis.py"
        subprocess.run([sys.executable, str(script_path)], cwd=project_root)
    
    # Try to open as NetCDF
    try:
        ds = xr.open_dataset(output_path)
        ds.close()
        assert True, "File is a valid NetCDF file"
    except Exception as e:
        pytest.fail(f"Failed to open file as NetCDF: {str(e)}")

@pytest.mark.integration
def test_modis_fetch_has_expected_variables():
    """Test that the output file contains expected variables."""
    output_path = project_root / "data" / "raw" / "modis.nc"
    
    # Ensure file exists
    if not output_path.exists():
        script_path = project_root / "code" / "01_fetch_modis.py"
        subprocess.run([sys.executable, str(script_path)], cwd=project_root)
    
    ds = xr.open_dataset(output_path)
    
    # Check for chlorophyll variable (could be chlor_a or chlorophyll_a)
    has_chlor = 'chlor_a' in ds.data_vars or 'chlorophyll_a' in ds.data_vars
    assert has_chlor, "Missing expected chlorophyll variable"
    
    # Check for spatial coordinates
    has_lat = 'latitude' in ds.coords or 'lat' in ds.coords
    has_lon = 'longitude' in ds.coords or 'lon' in ds.coords
    assert has_lat, "Missing latitude coordinate"
    assert has_lon, "Missing longitude coordinate"
    
    ds.close()

@pytest.mark.integration
def test_modis_fetch_has_metadata():
    """Test that the output file contains metadata attributes."""
    output_path = project_root / "data" / "raw" / "modis.nc"
    
    # Ensure file exists
    if not output_path.exists():
        script_path = project_root / "code" / "01_fetch_modis.py"
        subprocess.run([sys.executable, str(script_path)], cwd=project_root)
    
    ds = xr.open_dataset(output_path)
    
    # Check for source attribute
    has_source = 'source' in ds.attrs
    assert has_source, "Missing source metadata"
    
    # Verify it mentions MODIS
    assert 'MODIS' in ds.attrs['source'], "Source attribute should mention MODIS"
    
    ds.close()