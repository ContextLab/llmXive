"""
Unit tests for T015: Create aligned GeoTIFF stack output.
These tests verify the alignment logic and metadata generation.
"""
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

# Import the functions to test
from scripts.create_aligned_stack import (
    ensure_aligned_stack,
    validate_non_null_overlap,
    generate_metadata,
    get_file_checksum
)

@pytest.fixture
def temp_raster_dir(tmp_path):
    """Create a temporary directory with sample rasters."""
    # Create sample rasters
    profile = {
        'driver': 'GTiff',
        'height': 10,
        'width': 10,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:3857',
        'transform': from_bounds(0, 0, 100, 100, 10, 10),
        'nodata': -9999
    }

    # File 1: Reference
    path1 = tmp_path / "layer1.tif"
    with rasterio.open(path1, 'w', **profile) as dst:
        dst.write(np.ones((1, 10, 10), dtype='float32') * 10)

    # File 2: Different transform (should be resampled)
    profile2 = profile.copy()
    profile2['transform'] = from_bounds(0, 0, 200, 200, 20, 20) # Different resolution/extent
    path2 = tmp_path / "layer2.tif"
    with rasterio.open(path2, 'w', **profile2) as dst:
        dst.write(np.ones((1, 10, 10), dtype='float32') * 20)

    return tmp_path, path1, path2

def test_ensure_aligned_stack(temp_raster_dir):
    """Test that rasters are aligned to the reference."""
    tmp_path, path1, path2 = temp_raster_dir
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    input_files = [path1, path2]
    aligned = ensure_aligned_stack(input_files, output_dir, 'EPSG:3857')

    assert "layer1" in aligned
    assert "layer2" in aligned
    assert aligned["layer1"].exists()
    assert aligned["layer2"].exists()

    # Check dimensions match reference
    with rasterio.open(aligned["layer1"]) as src:
        w1, h1 = src.width, src.height
    
    with rasterio.open(aligned["layer2"]) as src:
        w2, h2 = src.width, src.height

    assert w1 == w2 == 10
    assert h1 == h2 == 10

def test_validate_non_null_overlap(temp_raster_dir):
    """Test overlap validation."""
    tmp_path, path1, path2 = temp_raster_dir
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create aligned files
    input_files = [path1, path2]
    aligned = ensure_aligned_stack(input_files, output_dir, 'EPSG:3857')

    # Should pass with full overlap
    assert validate_non_null_overlap(aligned, threshold=0.5)

    # Create a file with no overlap (all nodata)
    profile = {
        'driver': 'GTiff',
        'height': 10,
        'width': 10,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:3857',
        'transform': from_bounds(0, 0, 100, 100, 10, 10),
        'nodata': -9999
    }
    path_no_overlap = tmp_path / "layer3.tif"
    with rasterio.open(path_no_overlap, 'w', **profile) as dst:
        dst.write(np.ones((1, 10, 10), dtype='float32') * -9999) # All nodata

    aligned["layer3"] = path_no_overlap

    # Should fail with no overlap
    assert not validate_non_null_overlap(aligned, threshold=0.5)

def test_generate_metadata(temp_raster_dir):
    """Test metadata generation."""
    tmp_path, path1, path2 = temp_raster_dir
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    meta_path = tmp_path / "metadata.json"

    input_files = [path1, path2]
    aligned = ensure_aligned_stack(input_files, output_dir, 'EPSG:3857')

    generate_metadata(aligned, "Test City", meta_path)

    assert meta_path.exists()
    with open(meta_path) as f:
        meta = json.load(f)

    assert meta["city"] == "Test City"
    assert "layers" in meta
    assert len(meta["layers"]) == 2
    for layer in meta["layers"]:
        assert "checksum_sha256" in layer
        assert "path" in layer