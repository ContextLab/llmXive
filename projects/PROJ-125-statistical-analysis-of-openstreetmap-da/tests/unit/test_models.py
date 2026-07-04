"""
Unit tests for data models (CityBoundary, RasterCovariate, TemperatureRaster).
"""
import pytest
from pathlib import Path
import tempfile
import json

from code.models import CityBoundary, RasterCovariate, TemperatureRaster


class TestCityBoundary:
    def test_valid_creation(self):
        """Test creating a valid CityBoundary."""
        city = CityBoundary(
            name="New York",
            code="NYC_001",
            crs="EPSG:4326",
            bounds=[-74.2, 40.5, -73.7, 40.9]
        )
        assert city.name == "New York"
        assert city.code == "NYC_001"
        assert city.validate() is True

    def test_invalid_bounds_length(self):
        """Test that invalid bounds length raises error."""
        with pytest.raises(ValueError):
            CityBoundary(
                name="Test",
                code="T001",
                bounds=[0, 0, 1]  # Only 3 values
            )

    def test_invalid_bounds_order(self):
        """Test that invalid bounds order raises error."""
        with pytest.raises(ValueError):
            CityBoundary(
                name="Test",
                code="T001",
                bounds=[10, 10, 5, 5]  # min > max
            )

    def test_missing_name(self):
        """Test that missing name raises error."""
        with pytest.raises(ValueError):
            CityBoundary(name="", code="T001")

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        city = CityBoundary(
            name="Boston",
            code="BOS_001",
            crs="EPSG:3857",
            bounds=[-71.2, 42.2, -70.9, 42.5]
        )
        
        json_str = city.to_json()
        data = json.loads(json_str)
        
        assert data["name"] == "Boston"
        assert data["code"] == "BOS_001"
        
        # Test round-trip
        city2 = CityBoundary(**data)
        assert city2.name == city.name

    def test_save_and_load(self):
        """Test saving to and loading from file."""
        city = CityBoundary(
            name="Chicago",
            code="CHI_001",
            crs="EPSG:4326",
            bounds=[-87.9, 41.6, -87.5, 42.0]
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "city.json"
            city.save(path)
            
            assert path.exists()
            
            loaded = CityBoundary.load(path)
            assert loaded.name == city.name
            assert loaded.code == city.code


class TestRasterCovariate:
    def test_valid_creation(self):
        """Test creating a valid RasterCovariate."""
        cov = RasterCovariate(
            name="building_density",
            variable_type="building_density",
            source="OpenStreetMap",
            units="percent"
        )
        assert cov.name == "building_density"
        assert cov.validate() is True

    def test_invalid_resolution(self):
        """Test that non-positive resolution raises error."""
        with pytest.raises(ValueError):
            RasterCovariate(
                name="test",
                variable_type="test",
                source="test",
                resolution=-10
            )

    def test_missing_variable_type(self):
        """Test that missing variable_type raises error."""
        with pytest.raises(ValueError):
            RasterCovariate(
                name="test",
                variable_type="",
                source="test"
            )

    def test_factory_method(self):
        """Test factory method creation."""
        cov = RasterCovariate.from_osm_layer(
            name="tree_cover",
            variable_type="tree_cover",
            source="OpenStreetMap",
            units="percent"
        )
        assert cov.name == "tree_cover"
        assert cov.units == "percent"


class TestTemperatureRaster:
    def test_valid_creation(self):
        """Test creating a valid TemperatureRaster."""
        temp = TemperatureRaster(
            name="modis_lst_2023",
            source="MODIS",
            temporal_extent="2023-01-01/2023-12-31",
            cloud_coverage=5.5
        )
        assert temp.name == "modis_lst_2023"
        assert temp.source == "MODIS"
        assert temp.validate() is True

    def test_invalid_cloud_coverage(self):
        """Test that invalid cloud_coverage raises error."""
        with pytest.raises(ValueError):
            TemperatureRaster(
                name="test",
                source="MODIS",
                cloud_coverage=150.0
            )

        with pytest.raises(ValueError):
            TemperatureRaster(
                name="test",
                source="MODIS",
                cloud_coverage=-10.0
            )

    def test_missing_source(self):
        """Test that missing source raises error."""
        with pytest.raises(ValueError):
            TemperatureRaster(
                name="test",
                source="",
                temporal_extent="2023"
            )

    def test_factory_method(self):
        """Test factory method creation."""
        temp = TemperatureRaster.from_satellite_metadata(
            name="landsat_lst_summer",
            source="Landsat8",
            temporal_extent="2023-06-01/2023-08-31",
            cloud_coverage=12.0,
            units="Celsius"
        )
        assert temp.name == "landsat_lst_summer"
        assert temp.units == "Celsius"
        assert temp.cloud_coverage == 12.0
