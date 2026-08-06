"""
Unit tests for resampling functionality.

These tests verify that nearest-neighbor resampling preserves integer values
and handles various edge cases correctly.
"""
import os
import tempfile
import pytest
import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_bounds

# Import the function to test
from resampling import generate_resolution, run_resampling_pipeline


@pytest.fixture
def sample_raster():
    """Create a temporary sample raster for testing."""
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        # Create a simple raster with known integer values
        width = 100
        height = 100
        data = np.random.randint(0, 10, size=(height, width), dtype=np.uint8)
        
        transform = from_bounds(0, 0, 1, 1, width, height)
        
        profile = {
            'driver': 'GTiff',
            'height': height,
            'width': width,
            'count': 1,
            'dtype': 'uint8',
            'crs': 'EPSG:4326',
            'transform': transform
        }
        
        with rasterio.open(tmp.name, 'w', **profile) as dst:
            dst.write(data, 1)
        
        yield tmp.name
        
        # Cleanup
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_nearest_neighbor_preserves_integers(sample_raster):
    """
    Test that nearest-neighbor resampling preserves unique integer values.
    
    This is critical for categorical land cover data where interpolation
    would create invalid intermediate values.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = generate_resolution(sample_raster, factor=2, output_dir=tmpdir)
        
        # Read original data
        with rasterio.open(sample_raster) as src:
            original_data = src.read(1)
            original_unique = set(np.unique(original_data))
        
        # Read resampled data
        with rasterio.open(output_path) as src:
            resampled_data = src.read(1)
            resampled_unique = set(np.unique(resampled_data))
        
        # Assert that all resampled values exist in the original
        # (nearest-neighbor should not introduce new values)
        assert resampled_unique.issubset(original_unique), (
            f"Resampled data contains values not in original: "
            f"{resampled_unique - original_unique}"
        )
        
        # Verify that the number of unique values is reasonable
        # (may be fewer due to downsampling, but not more)
        assert len(resampled_unique) <= len(original_unique)


def test_resampling_reduces_dimensions(sample_raster):
    """Test that resampling correctly reduces image dimensions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Get original dimensions
        with rasterio.open(sample_raster) as src:
            original_width = src.width
            original_height = src.height
        
        # Test factor=2
        output_path = generate_resolution(sample_raster, factor=2, output_dir=tmpdir)
        
        with rasterio.open(output_path) as src:
            assert src.width == original_width // 2
            assert src.height == original_height // 2


def test_resampling_invalid_factor(sample_raster):
    """Test that invalid factors raise appropriate errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="factor must be >= 1"):
            generate_resolution(sample_raster, factor=0, output_dir=tmpdir)
        
        with pytest.raises(ValueError, match="factor must be >= 1"):
            generate_resolution(sample_raster, factor=-1, output_dir=tmpdir)


def test_resampling_nonexistent_file():
    """Test that missing input files raise FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            generate_resolution("/nonexistent/path.tif", factor=2, output_dir=tmpdir)


def test_resampling_preserves_dtype(sample_raster):
    """Test that resampling preserves the original data type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = generate_resolution(sample_raster, factor=2, output_dir=tmpdir)
        
        with rasterio.open(sample_raster) as src:
            original_dtype = src.dtypes[0]
        
        with rasterio.open(output_path) as src:
            resampled_dtype = src.dtypes[0]
        
        assert original_dtype == resampled_dtype


def test_run_resampling_pipeline():
    """Test the full pipeline with multiple factors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small test raster
        width = 50
        height = 50
        data = np.random.randint(0, 5, size=(height, width), dtype=np.uint8)
        
        input_file = Path(tmpdir) / "test_input.tif"
        transform = from_bounds(0, 0, 1, 1, width, height)
        
        profile = {
            'driver': 'GTiff',
            'height': height,
            'width': width,
            'count': 1,
            'dtype': 'uint8',
            'crs': 'EPSG:4326',
            'transform': transform
        }
        
        with rasterio.open(input_file, 'w', **profile) as dst:
            dst.write(data, 1)
        
        # Run pipeline
        output_paths = run_resampling_pipeline(
            str(input_file), 
            factors=[2, 4]
        )
        
        assert len(output_paths) == 2
        assert all(os.path.exists(p) for p in output_paths)
        
        # Verify dimensions
        with rasterio.open(input_file) as src:
            original_w, original_h = src.width, src.height
        
        for i, factor in enumerate([2, 4]):
            with rasterio.open(output_paths[i]) as src:
                assert src.width == original_w // factor
                assert src.height == original_h // factor
