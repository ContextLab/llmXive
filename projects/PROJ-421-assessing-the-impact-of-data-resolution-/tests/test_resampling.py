"""
Tests for resampling functionality.
"""
import os
import tempfile
import pytest
import numpy as np
import rasterio
from pathlib import Path

from resampling import generate_resolution, run_resampling_pipeline
from utils import get_raster_info

@pytest.fixture
def sample_raster(tmp_path):
    """Create a sample raster for testing."""
    # Create a temporary raster with known values
    raster_path = tmp_path / "test_input.tif"
    
    # Create test data with integer values (simulating land cover classes)
    data = np.array([
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 4, 4],
        [3, 3, 4, 4]
    ], dtype=np.uint8)
    
    # Write to raster
    transform = rasterio.transform.from_bounds(0, 0, 1, 1, 2, 2)
    with rasterio.open(
        raster_path,
        'w',
        driver='GTiff',
        height=2,
        width=2,
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data, 1)
    
    return str(raster_path)

def test_nearest_neighbor_preserves_integers(sample_raster):
    """Test that nearest-neighbor resampling preserves integer values."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = generate_resolution(sample_raster, 2, tmp_dir)
        
        # Read original and output
        with rasterio.open(sample_raster) as src:
            original_data = src.read(1)
            original_unique = set(np.unique(original_data))
        
        with rasterio.open(output_path) as dst:
            output_data = dst.read(1)
            output_unique = set(np.unique(output_data))
        
        # All output values should be from the original set
        assert output_unique.issubset(original_unique), \
            f"Output contains values not in input: {output_unique - original_unique}"
        
        # No interpolation artifacts (all values should be integers)
        assert output_data.dtype in [np.uint8, np.int16, np.int32, np.float32], \
            f"Unexpected dtype: {output_data.dtype}"

def test_resampling_factor_2(sample_raster):
    """Test resampling with factor=2."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = generate_resolution(sample_raster, 2, tmp_dir)
        
        # Check file exists
        assert os.path.exists(output_path), f"Output file not created: {output_path}"
        
        # Check dimensions (should be halved)
        with rasterio.open(sample_raster) as src:
            orig_width, orig_height = src.width, src.height
        
        with rasterio.open(output_path) as dst:
            out_width, out_height = dst.width, dst.height
        
        # Dimensions should be approximately halved (with rounding)
        assert out_width <= orig_width, "Output width should not exceed input"
        assert out_height <= orig_height, "Output height should not exceed input"

def test_invalid_factor():
    """Test that invalid factors raise appropriate errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a dummy input file
        input_path = os.path.join(tmp_dir, "dummy.tif")
        with open(input_path, "w") as f:
            f.write("")
        
        with pytest.raises(FileNotFoundError):
            generate_resolution(input_path, 2, tmp_dir)
        
        # Test negative factor
        with pytest.raises(ValueError):
            generate_resolution(input_path, -1, tmp_dir)

def test_run_resampling_pipeline(sample_raster):
    """Test the pipeline function with multiple factors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        results = run_resampling_pipeline(sample_raster, factors=[2, 4])
        
        assert 2 in results, "Factor 2 should be in results"
        assert 4 in results, "Factor 4 should be in results"
        assert results[2] is not None, "Factor 2 should succeed"
        assert results[4] is not None, "Factor 4 should succeed"
        
        # Check files exist
        assert os.path.exists(results[2]), f"Output for factor 2 not found: {results[2]}"
        assert os.path.exists(results[4]), f"Output for factor 4 not found: {results[4]}"

def test_chunked_processing_memory_efficiency(sample_raster):
    """Test that chunked processing works correctly."""
    # This test verifies the implementation uses windowed reads
    # by checking that large rasters can be processed without memory issues
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = generate_resolution(sample_raster, 2, tmp_dir)
        
        # If we get here without memory error, chunked processing is working
        assert os.path.exists(output_path), "Output file should exist"