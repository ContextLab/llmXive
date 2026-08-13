"""
Integration tests for stack_output.py (T015)

Tests the creation of aligned GeoTIFF stacks and metadata generation.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_bounds

from stack_output import (
    compute_file_checksum,
    generate_metadata,
    write_metadata_json,
    create_aligned_raster_stack,
    main
)
from config import get_path

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        raw_dir = tmpdir / "raw"
        processed_dir = tmpdir / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        yield raw_dir, processed_dir

@pytest.fixture
def sample_rasters(temp_dirs):
    """Create sample GeoTIFF rasters for testing."""
    raw_dir, _ = temp_dirs
    
    # Create two sample rasters with different origins and CRS
    # Raster 1: 10x10, resolution 10m, origin (0,0)
    data1 = np.random.rand(1, 10, 10).astype(np.float32) * 100
    profile1 = {
        'driver': 'GTiff',
        'height': 10,
        'width': 10,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:3857',
        'transform': from_bounds(0, 0, 100, 100, 10, 10),
        'nodata': -9999
    }
    path1 = raw_dir / "raster1.tif"
    with rasterio.open(path1, 'w', **profile1) as dst:
        dst.write(data1)
        
    # Raster 2: 5x5, resolution 20m, offset (50, 50) -> covers same area partially
    data2 = np.random.rand(1, 5, 5).astype(np.float32) * 50
    profile2 = {
        'driver': 'GTiff',
        'height': 5,
        'width': 5,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:4326', # Different CRS
        'transform': from_bounds(50, 50, 150, 150, 20, 20),
        'nodata': -9999
    }
    path2 = raw_dir / "raster2.tif"
    with rasterio.open(path2, 'w', **profile2) as dst:
        dst.write(data2)
        
    return [path1, path2]

def test_compute_file_checksum(sample_rasters):
    """Test checksum computation."""
    path = sample_rasters[0]
    checksum = compute_file_checksum(path)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)
    
    # Same file should produce same checksum
    checksum2 = compute_file_checksum(path)
    assert checksum == checksum2

def test_generate_metadata(sample_rasters, temp_dirs):
    """Test metadata generation."""
    raw_dir, processed_dir = temp_dirs
    
    # Create dummy output files
    output_files = [processed_dir / "out1.tif", processed_dir / "out2.tif"]
    for f in output_files:
        f.touch()
        
    metadata = generate_metadata(
        input_files=sample_rasters,
        output_files=output_files,
        city="test_city",
        crs="EPSG:3857",
        resolution=30.0,
        bounds={"minx": 0, "miny": 0, "maxx": 100, "maxy": 100}
    )
    
    assert "created_at" in metadata
    assert metadata["city"] == "test_city"
    assert metadata["crs"] == "EPSG:3857"
    assert len(metadata["input_files"]) == 2
    assert len(metadata["output_files"]) == 2
    assert "checksums" in metadata

def test_write_metadata_json(sample_rasters, temp_dirs):
    """Test writing metadata to JSON."""
    raw_dir, processed_dir = temp_dirs
    metadata_path = processed_dir / "metadata.json"
    
    metadata = generate_metadata(
        input_files=sample_rasters,
        output_files=[],
        city="test",
        crs="EPSG:4326",
        resolution=10.0,
        bounds={}
    )
    
    write_metadata_json(metadata, metadata_path)
    
    assert metadata_path.exists()
    with open(metadata_path) as f:
        loaded = json.load(f)
    assert loaded["city"] == "test"

def test_create_aligned_raster_stack(sample_rasters, temp_dirs):
    """Test creation of aligned raster stack."""
    raw_dir, processed_dir = temp_dirs
    input_paths = sample_rasters
    
    # This will attempt to reproject and align
    # Note: In a real test, we might mock the rasterio operations 
    # or use very small, simple rasters to avoid heavy computation.
    # For now, we assume the function runs without error.
    
    output_paths = create_aligned_raster_stack(
        input_rasters=input_paths,
        output_dir=processed_dir,
        target_crs="EPSG:3857",
        target_resolution=10.0,
        city_name="test"
    )
    
    assert len(output_paths) == len(input_paths)
    for p in output_paths:
        assert p.exists()
        # Verify it's a valid GeoTIFF
        with rasterio.open(p) as src:
            assert src.crs.to_epsg() == 3857
            assert src.res[0] == 10.0 # Approximate due to rounding

def test_main_with_sample_data(sample_rasters, temp_dirs, monkeypatch):
    """Test main function with sample data."""
    raw_dir, processed_dir = temp_dirs
    
    # Mock get_path to use our temp directories
    def mock_get_path(key):
        if key == "data_raw":
            return raw_dir
        elif key == "data_processed":
            return processed_dir
        elif key == "data_metadata":
            return processed_dir / "metadata.json"
        return Path(".")
        
    monkeypatch.setattr("stack_output.get_path", mock_get_path)
    
    # Mock get_city_crs to return a valid EPSG
    def mock_get_city_crs(city):
        return "EPSG:3857"
        
    monkeypatch.setattr("stack_output.get_city_crs", mock_get_city_crs)
    
    # Run main
    result = main()
    assert result == 0
    
    # Verify outputs
    assert (processed_dir / "metadata.json").exists()
    aligned_files = list(processed_dir.glob("*_aligned.tif"))
    assert len(aligned_files) == len(sample_rasters)