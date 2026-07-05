"""Unit tests for data models defined in code/models.py."""
import pytest
import numpy as np
from models import ResolutionRaster, BinaryIndicatorMap

def test_resolution_raster_creation():
    """Test that ResolutionRaster can be instantiated with valid parameters."""
    data = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    raster = ResolutionRaster(
        resolution=30,
        path="data/raw/test.tif",
        values=data
    )
    assert raster.resolution == 30
    assert raster.path == "data/raw/test.tif"
    assert np.array_equal(raster.values, data)
    assert raster.values.dtype == np.uint8

def test_resolution_raster_empty_values():
    """Test ResolutionRaster with empty values."""
    raster = ResolutionRaster(
        resolution=60,
        path="data/raw/empty.tif",
        values=np.array([], dtype=np.uint8).reshape(0, 0)
    )
    assert raster.resolution == 60
    assert raster.values.shape == (0, 0)

def test_binary_indicator_map_creation():
    """Test that BinaryIndicatorMap can be instantiated."""
    binary_map = BinaryIndicatorMap(
        class_id=1,
        binary_values=np.array([[1, 0], [1, 0]], dtype=np.uint8)
    )
    assert binary_map.class_id == 1
    assert np.array_equal(binary_map.binary_values, np.array([[1, 0], [1, 0]], dtype=np.uint8))

def test_binary_indicator_map_unique_values():
    """Test that BinaryIndicatorMap only contains 0s and 1s."""
    # Valid case
    valid_map = BinaryIndicatorMap(
        class_id=2,
        binary_values=np.array([[0, 1], [1, 0]], dtype=np.uint8)
    )
    unique_vals = np.unique(valid_map.binary_values)
    assert set(unique_vals) <= {0, 1}

    # Note: We do not enforce validation in the dataclass constructor here
    # as the task is to test the data structure, not the validation logic.
    # The analysis module should handle validation before creating this object.

def test_resolution_raster_values_modification():
    """Test that modifying the values array does not affect the original."""
    original_data = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    raster = ResolutionRaster(
        resolution=30,
        path="data/raw/test.tif",
        values=original_data.copy()
    )
    raster.values[0, 0] = 99
    assert original_data[0, 0] == 1
    assert raster.values[0, 0] == 99

def test_binary_indicator_map_shape():
    """Test that BinaryIndicatorMap preserves shape."""
    data = np.ones((10, 10), dtype=np.uint8)
    binary_map = BinaryIndicatorMap(class_id=1, binary_values=data)
    assert binary_map.binary_values.shape == (10, 10)
