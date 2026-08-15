"""
Unit tests for data models (CityBoundary, RasterCovariate, TemperatureRaster).
"""
import pytest
import json
from pathlib import Path
import tempfile
from shapely.geometry import Polygon

from models.city import CityBoundary
from models.raster import RasterCovariate, TemperatureRaster


class TestCityBoundary:
    def test_valid_creation(self):
        """Test creating a valid CityBoundary."""
        wkt = "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"
        city = CityBoundary(name="TestCity", wkt_geometry=wkt)
        assert city.name == "TestCity"
        assert city.crs is not None
        assert city.geometry.is_valid

    def test_invalid_geometry(self):
        """Test that invalid WKT raises ValueError."""
        with pytest.raises(ValueError):
            CityBoundary(name="BadCity", wkt_geometry="INVALID_WKT")

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        wkt = "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"
        city = CityBoundary(name="TestCity", wkt_geometry=wkt)
        data = city.to_dict()

        assert data["name"] == "TestCity"
        assert data["geometry_wkt"] == wkt

        restored = CityBoundary.from_dict(data)
        assert restored.name == city.name
        assert restored.geometry.wkt == city.geometry.wkt

    def test_validate(self):
        """Test validation logic."""
        wkt = "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"
        city = CityBoundary(name="TestCity", wkt_geometry=wkt)
        assert city.validate() is True

        city.name = ""
        with pytest.raises(ValueError):
            city.validate()

    def test_to_geojson(self):
        """Test GeoJSON conversion."""
        wkt = "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"
        city = CityBoundary(name="TestCity", wkt_geometry=wkt)
        geojson = city.to_geojson()

        assert geojson["type"] == "Feature"
        assert geojson["geometry"]["type"] == "Polygon"
        assert geojson["properties"]["name"] == "TestCity"


class TestRasterCovariate:
    def test_valid_creation(self, tmp_path):
        """Test creating a valid RasterCovariate."""
        fake_file = tmp_path / "covariate.tif"
        fake_file.touch()

        cov = RasterCovariate(
            name="test_cov", path=fake_file, description="Test covariate"
        )
        assert cov.name == "test_cov"
        assert cov.path == fake_file
        assert cov.resolution == 30.0

    def test_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        missing = tmp_path / "nonexistent.tif"
        with pytest.raises(FileNotFoundError):
            RasterCovariate(name="bad", path=missing)

    def test_to_dict_and_from_dict(self, tmp_path):
        """Test serialization and deserialization."""
        fake_file = tmp_path / "covariate.tif"
        fake_file.touch()

        cov = RasterCovariate(name="test", path=fake_file)
        data = cov.to_dict()

        assert data["name"] == "test"
        assert data["path"] == str(fake_file)

        restored = RasterCovariate.from_dict(data)
        assert restored.name == cov.name
        assert restored.path == cov.path

    def test_validate(self, tmp_path):
        """Test validation logic."""
        fake_file = tmp_path / "covariate.tif"
        fake_file.touch()

        cov = RasterCovariate(name="test", path=fake_file)
        assert cov.validate() is True

        cov.name = ""
        with pytest.raises(ValueError):
            cov.validate()


class TestTemperatureRaster:
    def test_valid_creation(self, tmp_path):
        """Test creating a valid TemperatureRaster."""
        fake_file = tmp_path / "temp.tif"
        fake_file.touch()

        temp = TemperatureRaster(
            path=fake_file,
            source_dataset="MODIS",
            acquisition_date="2023-06-01",
            cloud_cover=5.0,
        )
        assert temp.path == fake_file
        assert temp.source_dataset == "MODIS"
        assert temp.cloud_cover == 5.0

    def test_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        missing = tmp_path / "nonexistent.tif"
        with pytest.raises(FileNotFoundError):
            TemperatureRaster(path=missing)

    def test_invalid_cloud_cover(self, tmp_path):
        """Test that invalid cloud cover raises ValueError."""
        fake_file = tmp_path / "temp.tif"
        fake_file.touch()

        with pytest.raises(ValueError):
            TemperatureRaster(path=fake_file, cloud_cover=150.0)

    def test_to_dict_and_from_dict(self, tmp_path):
        """Test serialization and deserialization."""
        fake_file = tmp_path / "temp.tif"
        fake_file.touch()

        temp = TemperatureRaster(path=fake_file)
        data = temp.to_dict()

        assert data["path"] == str(fake_file)
        assert "crs" in data

        restored = TemperatureRaster.from_dict(data)
        assert restored.path == temp.path

    def test_validate(self, tmp_path):
        """Test validation logic."""
        fake_file = tmp_path / "temp.tif"
        fake_file.touch()

        temp = TemperatureRaster(path=fake_file)
        assert temp.validate() is True

        temp.resolution = -10.0
        with pytest.raises(ValueError):
            temp.validate()