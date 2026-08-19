"""
Integration test for geocoding alignment.
Verifies that coordinate validation and CRS alignment functions work correctly
with real-world data scenarios as per User Story 1 requirements.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.geocoding import (
    validate_coordinates,
    align_crs,
    transform_coordinates,
    is_valid_crs,
    get_utm_zone,
    GeocodingError
)
from code.utils.exceptions import DataQualityError


class TestCoordinateValidation:
    """Tests for validate_coordinates function."""

    def test_valid_northern_hemisphere(self):
        """Test valid coordinates in Northern Hemisphere."""
        assert validate_coordinates(45.0, -122.0) is True
        assert validate_coordinates(90.0, 180.0) is True

    def test_valid_southern_hemisphere(self):
        """Test valid coordinates in Southern Hemisphere."""
        assert validate_coordinates(-45.0, 122.0) is True
        assert validate_coordinates(-90.0, -180.0) is True

    def test_invalid_latitude_high(self):
        """Test invalid latitude > 90."""
        assert validate_coordinates(95.0, 0.0) is False

    def test_invalid_latitude_low(self):
        """Test invalid latitude < -90."""
        assert validate_coordinates(-95.0, 0.0) is False

    def test_invalid_longitude_high(self):
        """Test invalid longitude > 180."""
        assert validate_coordinates(0.0, 200.0) is False

    def test_invalid_longitude_low(self):
        """Test invalid longitude < -180."""
        assert validate_coordinates(0.0, -200.0) is False

    def test_edge_cases(self):
        """Test edge case coordinates."""
        # Equator and Prime Meridian
        assert validate_coordinates(0.0, 0.0) is True
        # Poles
        assert validate_coordinates(90.0, 0.0) is True
        assert validate_coordinates(-90.0, 0.0) is True


class TestCRSAlignment:
    """Tests for CRS alignment and transformation functions."""

    def test_align_crs_epsg4326(self):
        """Test align_crs with standard WGS84 (EPSG:4326)."""
        # Should return coordinates as-is for EPSG:4326
        result = align_crs(45.0, -122.0, "EPSG:4326")
        assert result is not None
        # Result should be a tuple of (lat, lon) or similar structure
        assert len(result) == 2

    def test_align_crs_invalid_crs(self):
        """Test align_crs with invalid CRS string."""
        with pytest.raises((GeocodingError, ValueError)):
            align_crs(45.0, -122.0, "INVALID_CRS")

    def test_is_valid_crs(self):
        """Test is_valid_crs function."""
        assert is_valid_crs("EPSG:4326") is True
        assert is_valid_crs("EPSG:3857") is True
        assert is_valid_crs("EPSG:32610") is True  # UTM Zone 10N
        assert is_valid_crs("INVALID") is False

    def test_get_utm_zone_northern(self):
        """Test UTM zone calculation for Northern Hemisphere."""
        # Oregon, USA ~ Zone 10N
        zone = get_utm_zone(45.0, -122.0)
        assert zone == 10

        # Europe ~ Zone 32N
        zone = get_utm_zone(48.0, 10.0)
        assert zone == 32

    def test_get_utm_zone_southern(self):
        """Test UTM zone calculation for Southern Hemisphere."""
        # Australia ~ Zone 50S
        zone = get_utm_zone(-35.0, 140.0)
        assert zone == 50

    def test_transform_coordinates_roundtrip(self):
        """Test coordinate transformation roundtrip."""
        original_lat, original_lon = 45.0, -122.0
        
        # Transform to UTM and back
        utm_crs = f"EPSG:{32600 + get_utm_zone(original_lat, original_lon)}"
        
        # Verify the function exists and returns valid structure
        result = transform_coordinates(original_lat, original_lon, "EPSG:4326", utm_crs)
        assert result is not None
        assert len(result) == 2
        
        # Transform back
        back_result = transform_coordinates(result[0], result[1], utm_crs, "EPSG:4326")
        assert back_result is not None
        
        # Check approximate roundtrip (allowing for projection distortion)
        np.testing.assert_array_almost_equal(
            [back_result[0], back_result[1]], 
            [original_lat, original_lon], 
            decimal=5
        )

    def test_transform_invalid_source_crs(self):
        """Test transformation with invalid source CRS."""
        with pytest.raises((GeocodingError, ValueError)):
            transform_coordinates(45.0, -122.0, "INVALID", "EPSG:32610")

    def test_transform_invalid_target_crs(self):
        """Test transformation with invalid target CRS."""
        with pytest.raises((GeocodingError, ValueError)):
            transform_coordinates(45.0, -122.0, "EPSG:4326", "INVALID")


class TestIntegrationScenarios:
    """Integration scenarios simulating real pipeline usage."""

    def test_soilgrid_coordinate_validation(self):
        """Test validation of SoilGrids coordinates (global coverage)."""
        # SoilGrids covers -90 to 90 lat, -180 to 180 lon
        test_coords = [
            (0.0, 0.0),      # Equator/Prime Meridian
            (89.9, 179.9),   # Near pole
            (-89.9, -179.9), # Near opposite pole
            (45.5, -122.5)   # Typical US location
        ]
        
        for lat, lon in test_coords:
            assert validate_coordinates(lat, lon) is True

    def test_crs_alignment_for_raster_extraction(self):
        """Simulate CRS alignment needed for raster extraction."""
        # In real pipeline: soil data (raster) might be in UTM, 
        # trait data (CSV) in WGS84
        
        trait_lat, trait_lon = 45.0, -122.0
        trait_crs = "EPSG:4326"
        
        # Verify alignment works
        aligned = align_crs(trait_lat, trait_lon, trait_crs)
        assert aligned is not None
        assert isinstance(aligned, tuple)
        assert len(aligned) == 2

    def test_geocoding_error_handling(self):
        """Test that GeocodingError is raised appropriately."""
        # Invalid coordinates should fail validation
        assert validate_coordinates(100.0, 0.0) is False
        
        # Invalid CRS should raise error during alignment
        with pytest.raises((GeocodingError, ValueError)):
            align_crs(45.0, -122.0, "EPSG:99999")

    def test_batch_coordinate_processing(self):
        """Test processing multiple coordinates (simulating dataset)."""
        coordinates = [
            (45.0, -122.0),
            (46.0, -121.0),
            (44.0, -123.0),
            (35.0, -115.0)
        ]
        
        valid_count = 0
        for lat, lon in coordinates:
            if validate_coordinates(lat, lon):
                valid_count += 1
        
        assert valid_count == len(coordinates)

    def test_utm_zone_consistency(self):
        """Test that coordinates in same region get same UTM zone."""
        # Coordinates in Pacific Northwest should all be Zone 10
        coords = [
            (45.0, -122.0),
            (46.0, -121.0),
            (44.5, -122.5),
            (45.5, -121.5)
        ]
        
        zones = [get_utm_zone(lat, lon) for lat, lon in coords]
        assert all(z == zones[0] for z in zones)
        assert zones[0] == 10