"""
Unit tests for the binary indicator transformation (Task T003).
"""

import numpy as np
import rasterio
from pathlib import Path

from binary_indicator import make_binary

def _count_class_pixels(raster_path: Path, class_id: int) -> int:
    """Utility to count the number of pixels equal to ``class_id``."""
    with rasterio.open(raster_path) as src:
        data = src.read(1, masked=False)
        return int(np.sum(data == class_id))

def test_binary_forest_and_urban_counts(tmp_path):
    """
    Integration test that verifies:
    - The binary raster contains only values {0, 1, nodata}.
    - The number of 1‑pixels matches the count of the target class in the source raster.
    """
    # Create a tiny synthetic source raster for testing purposes.
    src_path = tmp_path / "source.tif"
    profile = {
        "driver": "GTiff",
        "dtype": rasterio.uint8,
        "width": 5,
        "height": 5,
        "count": 1,
        "crs": "EPSG:5070",
        "transform": rasterio.transform.from_origin(0, 5, 30, 30),
        "nodata": 0,
    }
    data = np.array([
        [41, 12, 41, 0, 12],
        [12, 41, 0, 12, 41],
        [41, 0, 12, 41, 12],
        [0, 12, 41, 0, 41],
        [12, 41, 12, 41, 0],
    ], dtype=np.uint8)

    with rasterio.open(src_path, "w", **profile) as dst:
        dst.write(data, 1)

    # Test forest (class 41)
    forest_binary = tmp_path / "binary_forest.tif"
    make_binary(src_path, 41, forest_binary)

    with rasterio.open(forest_binary) as src:
        binary_data = src.read(1, masked=False)
        unique_vals = set(np.unique(binary_data))
        assert unique_vals.issubset({0, 1, src.nodata}), "Binary raster contains unexpected values"

    forest_count_src = _count_class_pixels(src_path, 41)
    forest_count_bin = _count_class_pixels(forest_binary, 1)
    assert forest_count_src == forest_count_bin, "Forest 1‑pixel count mismatch"

    # Test urban (class 12)
    urban_binary = tmp_path / "binary_urban.tif"
    make_binary(src_path, 12, urban_binary)

    with rasterio.open(urban_binary) as src:
        binary_data = src.read(1, masked=False)
        unique_vals = set(np.unique(binary_data))
        assert unique_vals.issubset({0, 1, src.nodata}), "Binary raster contains unexpected values"

    urban_count_src = _count_class_pixels(src_path, 12)
    urban_count_bin = _count_class_pixels(urban_binary, 1)
    assert urban_count_src == urban_count_bin, "Urban 1‑pixel count mismatch"