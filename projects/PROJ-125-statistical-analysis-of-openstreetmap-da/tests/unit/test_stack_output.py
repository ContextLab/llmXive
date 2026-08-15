"""
Unit tests for stack_output.py (Task T015).
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

# Import module under test
from stack_output import (
    compute_file_checksum,
    generate_metadata,
    write_metadata_json,
    create_aligned_raster_stack
)
from config import get_path

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_raster(temp_dir):
    """Create a small dummy GeoTIFF for testing."""
    path = temp_dir / "sample.tif"
    data = np.random.rand(1, 10, 10).astype(np.float32)
    transform = from_bounds(0, 0, 10, 10, 10, 10)
    
    with rasterio.open(
        path, 'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data)
    return path

def test_compute_file_checksum(temp_dir, sample_raster):
    """Test checksum computation."""
    checksum = compute_file_checksum(sample_raster)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length

def test_generate_metadata(temp_dir, sample_raster):
    """Test metadata generation."""
    output_file = temp_dir / "out.tif"
    output_file.touch() # Create dummy output

    meta = generate_metadata(
        input_files=[sample_raster],
        output_files=[output_file],
        city_name="TestCity",
        crs="EPSG:3857",
        resolution=30.0
    )

    assert meta["city"] == "TestCity"
    assert len(meta["input_files"]) == 1
    assert "checksum" in meta["input_files"][0]
    assert "generated_at" in meta

def test_write_metadata_json(temp_dir):
    """Test writing metadata to JSON."""
    meta = {"test": "value", "number": 42}
    out_path = temp_dir / "meta.json"
    
    write_metadata_json(meta, out_path)
    
    assert out_path.exists()
    with open(out_path) as f:
        loaded = json.load(f)
    assert loaded == meta

@patch('stack_output.get_city_bounds')
@patch('stack_output.get_city_crs')
@patch('stack_output.get_path')
def test_create_aligned_raster_stack(
    mock_get_path, mock_get_crs, mock_get_bounds, temp_dir, sample_raster
):
    """Test the full alignment pipeline with mocked config."""
    # Setup mocks
    mock_get_path.side_effect = lambda x: temp_dir if "processed" in x else temp_dir.parent
    mock_get_crs.return_value = "EPSG:32618"
    
    # Mock a simple polygon for bounds
    from shapely.geometry import box
    mock_get_bounds.return_value = box(-74.0, 40.5, -73.9, 40.6)

    input_rasters = [{"path": str(sample_raster), "type": "covariate"}]
    
    # Run the function
    output_paths = create_aligned_raster_stack(
        city_name="TestCity",
        input_rasters=input_rasters,
        output_dir=temp_dir
    )

    assert len(output_paths) == 1
    assert output_paths[0].exists()
    assert output_paths[0].suffix == ".tif"

    # Verify the output has the correct CRS and transform (approx)
    with rasterio.open(output_paths[0]) as src:
        assert src.crs.to_string() == "EPSG:32618"
        # Check dimensions are reasonable (not 10x10 anymore due to reprojection/resampling)
        assert src.width > 0
        assert src.height > 0