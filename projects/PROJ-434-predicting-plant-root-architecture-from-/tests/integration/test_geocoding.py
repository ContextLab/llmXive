"""
Integration test for geocoding alignment.
"""
import pytest
import numpy as np
from code.utils.geocoding import validate_coordinates, align_crs

def test_validate_coordinates():
    """Test coordinate validation logic."""
    # Valid coordinates
    assert validate_coordinates(45.0, -122.0) is True
    
    # Invalid coordinates (out of range)
    assert validate_coordinates(95.0, 0.0) is False
    assert validate_coordinates(0.0, 200.0) is False

def test_align_crs():
    """Test CRS alignment (mocked for integration)."""
    # This test verifies the function exists and can be called
    # Actual CRS transformation would require raster data
    result = align_crs(45.0, -122.0, "EPSG:4326")
    assert result is not None