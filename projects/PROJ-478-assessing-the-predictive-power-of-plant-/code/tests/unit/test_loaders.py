"""
Unit tests for src/data/loaders.py
"""

import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from affine import Affine

import rasterio
from rasterio.crs import CRS

from src.data.loaders import (
    load_raster,
    check_coordinate_alignment,
    load_rasters_aligned,
    extract_raster_values,
    load_climate_rasters_for_species,
    check_raster_coverage
)

# Fixtures
@pytest.fixture
def temp_raster_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def create_test_raster(
    path: Path,
    shape: tuple = (10, 10),
    transform: Affine = None,
    crs: CRS = None,
    values: np.ndarray = None
) -> rasterio.DatasetReader:
    """Helper to create a test raster file."""
    if transform is None:
        transform = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    if crs is None:
        crs = CRS.from_epsg(4326)
    if values is None:
        values = np.random.rand(*shape).astype(np.float32)

    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=shape[0],
        width=shape[1],
        count=1,
        dtype=values.dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(values, 1)
    return rasterio.open(path)

def test_load_raster_success(temp_raster_dir):
    raster_path = temp_raster_dir / "test.tif"
    create_test_raster(raster_path)

    data, src = load_raster(raster_path)

    assert data.shape[1:] == (10, 10)  # height, width
    assert src.crs == CRS.from_epsg(4326)
    src.close()

def test_load_raster_not_found():
    with pytest.raises(FileNotFoundError):
        load_raster("non_existent_file.tif")

def test_load_rasters_aligned(temp_raster_dir):
    # Create two aligned rasters
    r1_path = temp_raster_dir / "r1.tif"
    r2_path = temp_raster_dir / "r2.tif"

    t = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    create_test_raster(r1_path, transform=t)
    create_test_raster(r2_path, transform=t)

    arrays, datasets = load_rasters_aligned([r1_path, r2_path])

    assert len(arrays) == 2
    assert len(datasets) == 2
    for ds in datasets:
        ds.close()

def test_check_coordinate_alignment_success(temp_raster_dir):
    t = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    r1 = create_test_raster(temp_raster_dir / "r1.tif", transform=t)
    r2 = create_test_raster(temp_raster_dir / "r2.tif", transform=t)

    assert check_coordinate_alignment([r1, r2]) is True
    r1.close()
    r2.close()

def test_check_coordinate_alignment_crs_mismatch(temp_raster_dir):
    t = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    r1 = create_test_raster(temp_raster_dir / "r1.tif", transform=t, crs=CRS.from_epsg(4326))
    # Create second with different CRS
    r2 = create_test_raster(temp_raster_dir / "r2.tif", transform=t, crs=CRS.from_epsg(3857))

    assert check_coordinate_alignment([r1, r2]) is False
    r1.close()
    r2.close()

def test_extract_raster_values(temp_raster_dir):
    # Create a raster with known values
    raster_path = temp_raster_dir / "test.tif"
    shape = (10, 10)
    transform = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    # Create a simple gradient
    values = np.arange(100).reshape(shape).astype(np.float32)
    create_test_raster(raster_path, shape=shape, transform=transform, values=values)

    _, src = load_raster(raster_path)

    # Create occurrences at specific coordinates
    # Top-left is (0, 0) -> row 0, col 0 -> value 0
    # (1, -1) -> row 1, col 1 -> value 11 (row 1, col 1 in 10x10 array)
    occurrences = pd.DataFrame({
        'decimalLongitude': [0.0, 1.0],
        'decimalLatitude': [0.0, -1.0]
    })

    result = extract_raster_values(src.read(1), src.transform, occurrences)

    # Check values
    # Note: rasterio read returns (band, h, w). src.read(1) is 2D.
    # Row 0, Col 0 is value 0.
    # Row 1, Col 1 is value 11 (1*10 + 1).
    assert result['value'].iloc[0] == 0.0
    assert result['value'].iloc[1] == 11.0
    src.close()

def test_load_climate_rasters_for_species(temp_raster_dir):
    # Setup
    # 1. Create occurrence file
    occ_path = temp_raster_dir / "occ.csv"
    occ_df = pd.DataFrame({
        'species': ['A', 'A'],
        'decimalLongitude': [0.0, 5.0],
        'decimalLatitude': [0.0, -5.0]
    })
    occ_df.to_csv(occ_path, index=False)

    # 2. Create rasters
    climate_dir = temp_raster_dir / "climate"
    climate_dir.mkdir()

    t = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    # Create a raster where value = lon * 10 + lat * 10 (simplified)
    # We'll just create a random one and check it loads
    create_test_raster(climate_dir / "bio1.tif", transform=t)
    create_test_raster(climate_dir / "bio2.tif", transform=t)

    # 3. Run function
    result = load_climate_rasters_for_species(
        species_id="A",
        occurrence_path=occ_path,
        climate_dir=climate_dir
    )

    # 4. Verify
    assert 'bio1' in result.columns or 'band_0' in result.columns
    assert len(result) == 2

def test_check_raster_coverage(temp_raster_dir):
    # Create occurrence file
    occ_path = temp_raster_dir / "occ.csv"
    occ_df = pd.DataFrame({
        'decimalLongitude': [0.0, 10.0, 20.0],
        'decimalLatitude': [0.0, 0.0, 0.0]
    })
    occ_df.to_csv(occ_path, index=False)

    # Create rasters
    r1_path = temp_raster_dir / "r1.tif"
    # Raster covering 0 to 5
    t = Affine(1.0, 0.0, 0.0, 0.0, 0.0, -1.0)
    create_test_raster(r1_path, shape=(10, 10), transform=t) # Covers 0..10 in X, 0..-10 in Y

    # Raster covering 15 to 25 (shifted)
    t2 = Affine(1.0, 0.0, 15.0, 0.0, 0.0, -1.0)
    r2_path = temp_raster_dir / "r2.tif"
    create_test_raster(r2_path, shape=(10, 10), transform=t2)

    result = check_raster_coverage(
        occurrence_path=occ_path,
        raster_paths=[r1_path, r2_path]
    )

    assert result['total_points'] == 3
    # Point at 20 is covered by r2. Points at 0 and 10 covered by r1.
    # All covered?
    assert result['fully_covered'] is True