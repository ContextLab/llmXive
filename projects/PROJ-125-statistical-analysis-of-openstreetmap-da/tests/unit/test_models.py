"""
Unit tests for data models in code/models/.

These tests verify:
- CityBoundary geometry validation
- RasterCovariate file existence and stats computation
- TemperatureRaster unit conversion
- Serialization/deserialization
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np

# Import models
from code.models.city_boundary import CityBoundary
from code.models.raster_covariate import RasterCovariate
from code.models.temperature_raster import TemperatureRaster


class TestCityBoundary:
    """Tests for CityBoundary model."""

    def test_valid_initialization(self):
        """Test initialization with valid WKT."""
        wkt = "POLYGON((-74.0 40.7, -74.0 40.8, -73.9 40.8, -73.9 40.7, -74.0 40.7))"
        city = CityBoundary(
            city_name="New York",
            wkt_geometry=wkt,
            crs_epsg=4326,
            source="OpenStreetMap"
        )
        assert city.city_name == "New York"
        assert city.crs_epsg == 4326
        assert city.source == "OpenStreetMap"
        assert city.bbox is not None
        assert len(city.bbox) == 4

    def test_invalid_geometry_type(self):
        """Test that non-polygon geometry raises error."""
        wkt = "POINT(-74.0 40.7)"
        with pytest.raises(ValueError):
            CityBoundary(
                city_name="Test",
                wkt_geometry=wkt,
                crs_epsg=4326
            )

    def test_invalid_crs(self):
        """Test that invalid EPSG code raises error."""
        wkt = "POLYGON((-74.0 40.7, -74.0 40.8, -73.9 40.8, -73.9 40.7, -74.0 40.7))"
        with pytest.raises(ValueError):
            CityBoundary(
                city_name="Test",
                wkt_geometry=wkt,
                crs_epsg=-1
            )

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        wkt = "POLYGON((-74.0 40.7, -74.0 40.8, -73.9 40.8, -73.9 40.7, -74.0 40.7))"
        city = CityBoundary(
            city_name="New York",
            wkt_geometry=wkt,
            crs_epsg=4326
        )
        
        json_str = city.to_json()
        data = json.loads(json_str)
        assert data['city_name'] == "New York"
        assert data['crs_epsg'] == 4326

        # Test loading from dict
        city2 = CityBoundary(**data)
        assert city2.city_name == city.city_name


class TestRasterCovariate:
    """Tests for RasterCovariate model."""

    def test_file_not_found(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            RasterCovariate(
                name="test_covariate",
                file_path="/nonexistent/path.tif",
                crs_epsg=4326,
                resolution_m=30.0
            )

    def test_stats_computation(self):
        """Test that stats are computed automatically."""
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            # Create a minimal GeoTIFF
            try:
                import rasterio
                from rasterio.transform import from_bounds
                import numpy as np

                data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float32)
                transform = from_bounds(0, 0, 3, 3, 3, 3)
                
                with rasterio.open(
                    tmp.name, 'w',
                    driver='GTiff',
                    height=3, width=3,
                    count=1,
                    dtype=data.dtype,
                    crs='EPSG:4326',
                    transform=transform
                ) as dst:
                    dst.write(data, 1)

                cov = RasterCovariate(
                    name="test_cov",
                    file_path=tmp.name,
                    crs_epsg=4326,
                    resolution_m=1.0
                )
                
                assert cov.stats is not None
                assert cov.stats['mean'] == 5.0
                assert cov.stats['count'] == 9
            finally:
                os.unlink(tmp.name)


class TestTemperatureRaster:
    """Tests for TemperatureRaster model."""

    def test_unit_conversion(self):
        """Test Kelvin to Celsius conversion."""
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            try:
                import rasterio
                from rasterio.transform import from_bounds
                import numpy as np

                # Create data in Kelvin
                data = np.array([[300, 301, 302], [303, 304, 305]], dtype=np.float32)
                transform = from_bounds(0, 0, 3, 2, 3, 2)
                
                with rasterio.open(
                    tmp.name, 'w',
                    driver='GTiff',
                    height=2, width=3,
                    count=1,
                    dtype=data.dtype,
                    crs='EPSG:4326',
                    transform=transform
                ) as dst:
                    dst.write(data, 1)

                temp_raster = TemperatureRaster(
                    name="test_temp",
                    file_path=tmp.name,
                    crs_epsg=4326,
                    resolution_m=1.0,
                    unit="K"
                )
                
                # Convert to Celsius
                temp_c = temp_raster.convert_units("C")
                assert temp_c.unit == "C"
                # Mean should be around 27-28 C (300-305 K)
                assert 20 < temp_c.stats['mean_temp_c'] < 35
            finally:
                os.unlink(tmp.name)

    def test_missing_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError):
            TemperatureRaster.load_from_file("nonexistent.json")