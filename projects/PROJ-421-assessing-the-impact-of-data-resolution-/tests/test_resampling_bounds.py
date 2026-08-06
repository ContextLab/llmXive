"""
Unit tests for bounds checking in resampling.py
"""
import pytest
import os
import tempfile
import numpy as np
import rasterio
from pathlib import Path

# Import the function to test
from resampling import generate_resolution

@pytest.fixture
def small_raster(tmp_path):
    """Create a small test raster for bounds checking."""
    filepath = tmp_path / "test_small.tif"
    data = np.random.randint(1, 10, size=(1, 100, 100), dtype=np.uint8)
    transform = rasterio.transform.from_bounds(0, 0, 100, 100, 100, 100)
    
    with rasterio.open(
        filepath, 'w',
        driver='GTiff',
        height=100,
        width=100,
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data)
    return str(filepath)

@pytest.fixture
def tiny_raster(tmp_path):
    """Create a very small raster that will fail high factors."""
    filepath = tmp_path / "test_tiny.tif"
    data = np.random.randint(1, 10, size=(1, 10, 10), dtype=np.uint8)
    transform = rasterio.transform.from_bounds(0, 0, 10, 10, 10, 10)
    
    with rasterio.open(
        filepath, 'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data)
    return str(filepath)

def test_nearest_neighbor_preserves_integers(small_raster, tmp_path):
    """Test that nearest-neighbor resampling preserves unique integer values."""
    output_path = tmp_path / "output.tif"
    # Factor 2 on 100x100 -> 50x50 (valid)
    result = generate_resolution(small_raster, 2)
    assert result is not None, "Generation should succeed for valid factor"
    
    # Read output and check unique values
    with rasterio.open(result) as src:
        output_data = src.read(1)
    
    with rasterio.open(small_raster) as src:
        input_data = src.read(1)
    
    # Ensure unique values are preserved (subset or equal)
    input_unique = set(np.unique(input_data))
    output_unique = set(np.unique(output_data))
    
    # Output unique values must be a subset of input unique values
    assert output_unique.issubset(input_unique), \
        f"Output values {output_unique} not subset of input {input_unique}"

def test_bounds_check_skips_invalid_factor(tiny_raster, tmp_path):
    """Test that factors resulting in zero/negative dimensions are skipped."""
    # Factor 20 on 10x10 -> 0.5 (should floor to 0 or negative logic)
    # 10 // 20 = 0 -> Invalid
    result = generate_resolution(tiny_raster, 20)
    assert result is None, "Should return None for invalid factor resulting in 0 dimensions"

def test_bounds_check_valid_factor(tiny_raster, tmp_path):
    """Test that valid factors still work on small rasters."""
    # Factor 2 on 10x10 -> 5x5 (valid)
    result = generate_resolution(tiny_raster, 2)
    assert result is not None, "Should succeed for valid factor"
    
    assert os.path.exists(result), "Output file should exist"

def test_invalid_input_path():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        generate_resolution("/nonexistent/path.tif", 2)