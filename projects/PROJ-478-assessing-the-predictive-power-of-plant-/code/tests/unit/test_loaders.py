import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import rasterio
from rasterio.transform import from_bounds
from shapely.geometry import Point
import geopandas as gpd

from src.data.loaders import (
    load_raster,
    load_rasters_aligned,
    check_coordinate_alignment,
    extract_raster_values,
    load_climate_rasters_for_species
)


@pytest.fixture
def temp_raster_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_raster(path, width=10, height=10, transform=None, crs="EPSG:4326", data=None):
    """Helper to create a simple test GeoTIFF."""
    if transform is None:
        # Default: 1 degree resolution, top-left at (-180, 90)
        transform = from_bounds(-180, -90, 180, 90, width, height)
    
    if data is None:
        data = np.ones((height, width), dtype=np.float32) * 5.0

    with rasterio.open(
        path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(data, 1)


def test_load_raster_success(temp_raster_dir):
    raster_path = temp_raster_dir / "test.tif"
    create_test_raster(raster_path)
    
    data, meta, crs = load_raster(raster_path)
    
    assert data.shape == (10, 10)
    assert np.all(data == 5.0)
    assert str(crs) == "EPSG:4326"
    assert 'transform' in meta


def test_load_raster_not_found():
    with pytest.raises(FileNotFoundError):
        load_raster("non_existent_file.tif")


def test_load_rasters_aligned(temp_raster_dir):
    # Create two identical rasters
    path1 = temp_raster_dir / "r1.tif"
    path2 = temp_raster_dir / "r2.tif"
    create_test_raster(path1)
    create_test_raster(path2)
    
    data_list, meta = load_rasters_aligned([path1, path2], path1)
    
    assert len(data_list) == 2
    assert data_list[0].shape == (10, 10)
    assert np.all(data_list[0] == 5.0)
    assert np.all(data_list[1] == 5.0)


def test_check_coordinate_alignment_success(temp_raster_dir):
    raster_path = temp_raster_dir / "test.tif"
    create_test_raster(raster_path, width=10, height=10, transform=from_bounds(-10, -10, 10, 10, 10, 10))
    
    _, meta, _ = load_raster(raster_path)
    
    # Create points inside the extent
    points = gpd.GeoDataFrame(
        geometry=[Point(0, 0), Point(5, 5)],
        crs="EPSG:4326"
    )
    
    assert check_coordinate_alignment(points, meta) is True


def test_check_coordinate_alignment_crs_mismatch(temp_raster_dir):
    raster_path = temp_raster_dir / "test.tif"
    create_test_raster(raster_path)
    
    _, meta, _ = load_raster(raster_path)
    
    # Create points with different CRS
    points = gpd.GeoDataFrame(
        geometry=[Point(0, 0)],
        crs="EPSG:3857"
    )
    
    assert check_coordinate_alignment(points, meta) is False


def test_extract_raster_values(temp_raster_dir):
    raster_path = temp_raster_dir / "test.tif"
    # Create raster with known values
    data = np.arange(100, dtype=np.float32).reshape(10, 10)
    create_test_raster(raster_path, data=data, transform=from_bounds(-5, -5, 5, 5, 10, 10))
    
    _, meta, _ = load_raster(raster_path)
    
    # Create a point at a known location
    # If transform is from_bounds(-5, -5, 5, 5, 10, 10), then:
    # x0=-5, y0=5 (top), xres=1, yres=-1
    # Point (0, 0) should be at row=5, col=5 -> value 55
    points = gpd.GeoDataFrame(
        geometry=[Point(0, 0)],
        crs="EPSG:4326"
    )
    
    aligned_data = [data]
    df = extract_raster_values(aligned_data, points, meta)
    
    assert len(df) == 1
    # The value at (0,0) in the generated data (row 5, col 5) is 55
    # Note: rasterio indexing is [row, col]
    # row 5, col 5 -> index 55 in flattened array
    assert df['raster_0'].iloc[0] == 55.0


def test_load_climate_rasters_for_species(temp_raster_dir):
    # Create a raster
    raster_path = temp_raster_dir / "bio1.tif"
    create_test_raster(raster_path, width=10, height=10, transform=from_bounds(-5, -5, 5, 5, 10, 10))
    
    # Create occurrences
    points = gpd.GeoDataFrame(
        geometry=[Point(0, 0), Point(2, 2)],
        crs="EPSG:4326"
    )
    
    df = load_climate_rasters_for_species(points, temp_raster_dir)
    
    assert 'occurrence_id' in df.columns
    assert 'bio1' in df.columns
    assert len(df) == 2