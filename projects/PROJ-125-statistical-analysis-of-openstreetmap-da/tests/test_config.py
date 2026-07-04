"""
Unit tests for code/config.py
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import (
    get_city_bounds,
    get_city_crs,
    CITIES,
    MAX_BLOCKS,
    CRS_STORAGE,
    get_path,
    DATA_DIR
)

class TestCityConfig:
    def test_get_city_bounds_valid(self):
        """Test retrieving bounds for a valid city."""
        bounds = get_city_bounds("new_york")
        assert len(bounds) == 4
        assert bounds[0] < bounds[2]  # minx < maxx
        assert bounds[1] < bounds[3]  # miny < maxy
        # Check approximate values for NYC
        assert -74.3 < bounds[0] < -73.7
        assert 40.4 < bounds[1] < 40.9

    def test_get_city_bounds_invalid(self):
        """Test retrieving bounds for an invalid city raises KeyError."""
        with pytest.raises(KeyError):
            get_city_bounds("nonexistent_city")

    def test_get_city_crs_new_york(self):
        """Test UTM CRS calculation for New York."""
        crs = get_city_crs("new_york")
        # NYC is in UTM Zone 18N -> EPSG 32618
        assert crs == 32618

    def test_get_city_crs_los_angeles(self):
        """Test UTM CRS calculation for Los Angeles."""
        crs = get_city_crs("los_angeles")
        # LA is in UTM Zone 11N -> EPSG 32611
        assert crs == 32611

    def test_max_blocks_constant(self):
        """Test that MAX_BLOCKS is set to 100."""
        assert MAX_BLOCKS == 100

    def test_crs_storage_constant(self):
        """Test that CRS_STORAGE is set to 3857."""
        assert CRS_STORAGE == 3857

    def test_get_path_relative(self):
        """Test get_path function with relative path."""
        p = get_path("data/raw/test.csv")
        assert isinstance(p, Path)
        assert "data" in str(p)
        assert "raw" in str(p)

    def test_cities_dict_structure(self):
        """Test that CITIES dictionary has the expected structure."""
        for city_key, city_data in CITIES.items():
            assert "name" in city_data
            assert "bounds_4326" in city_data
            assert "description" in city_data
            bounds = city_data["bounds_4326"]
            assert len(bounds) == 4