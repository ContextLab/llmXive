"""
Unit tests for data models (CityBoundary, RasterCovariate, TemperatureRaster).
"""
import pytest
import json
import tempfile
from pathlib import Path
from shapely.geometry import box, mapping

from code.models.base import BaseModel
from code.models.city import CityBoundary
from code.models.raster import RasterCovariate, TemperatureRaster


class TestBaseModel:
    """Tests for the BaseModel base class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Create a simple subclass for testing
        class TestModel(BaseModel):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        model = TestModel(1, 2)
        data = model.to_dict()
        assert data == {"a": 1, "b": 2}

    def test_to_json(self):
        """Test JSON serialization."""
        class TestModel(BaseModel):
            def __init__(self, name, value):
                self.name = name
                self.value = value

        model = TestModel("test", 42)
        json_str = model.to_json()
        parsed = json.loads(json_str)
        assert parsed == {"name": "test", "value": 42}

    def test_validate_schema_missing_field(self):
        """Test validation raises error for missing fields."""
        data = {"a": 1}
        with pytest.raises(ValueError) as exc_info:
            BaseModel.validate_schema(data, ["a", "b"])
        assert "Missing required fields" in str(exc_info.value)
        assert "b" in str(exc_info.value)

    def test_validate_schema_all_present(self):
        """Test validation passes when all fields present."""
        data = {"a": 1, "b": 2}
        try:
            BaseModel.validate_schema(data, ["a", "b"])
        except ValueError:
            pytest.fail("Validation should not raise for complete data")


class TestCityBoundary:
    """Tests for CityBoundary model."""

    @pytest.fixture
    def sample_polygon(self):
        """Create a sample polygon WKT."""
        # Simple square polygon
        return "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"

    def test_init_valid(self, sample_polygon):
        """Test initialization with valid data."""
        city = CityBoundary(
            city_name="New York",
            country="USA",
            geometry=sample_polygon,
            epsg_code=4326,
            source="OSM"
        )
        assert city.city_name == "New York"
        assert city.country == "USA"
        assert city.epsg_code == 4326

    def test_init_missing_required(self, sample_polygon):
        """Test initialization fails without required fields."""
        with pytest.raises(ValueError):
            CityBoundary(
                city_name="Test",
                country="USA",
                geometry="", # Empty geometry
            )

    def test_shapely_geom_property(self, sample_polygon):
        """Test conversion to Shapely geometry."""
        city = CityBoundary(
            city_name="Test",
            country="USA",
            geometry=sample_polygon
        )
        geom = city.shapely_geom
        assert geom.area == 1.0
        assert geom.is_valid

    def test_bbox_property(self, sample_polygon):
        """Test bounding box calculation."""
        city = CityBoundary(
            city_name="Test",
            country="USA",
            geometry=sample_polygon
        )
        bbox = city.bbox
        assert bbox == (0.0, 0.0, 1.0, 1.0)

    def test_to_geojson(self, sample_polygon):
        """Test GeoJSON conversion."""
        city = CityBoundary(
            city_name="Test",
            country="USA",
            geometry=sample_polygon,
            area_km2=100.0
        )
        gj = city.to_geojson()
        assert gj["type"] == "Feature"
        assert gj["properties"]["city_name"] == "Test"
        assert gj["geometry"]["type"] == "Polygon"

    def test_save_and_load(self, sample_polygon, tmp_path):
        """Test saving to and loading from file."""
        city = CityBoundary(
            city_name="Test",
            country="USA",
            geometry=sample_polygon,
            source="OSM"
        )
        file_path = tmp_path / "city.json"
        city.save(file_path)
        
        loaded = CityBoundary.load(file_path)
        assert loaded.city_name == city.city_name
        assert loaded.geometry == city.geometry


class TestRasterCovariate:
    """Tests for RasterCovariate model."""

    def test_init_valid(self):
        """Test initialization with valid data."""
        raster = RasterCovariate(
            name="building_density",
            description="Building footprint density",
            source="OSM",
            path="/fake/path.tif",
            crs=3857,
            resolution=30.0
        )
        assert raster.name == "building_density"
        assert raster.resolution == 30.0
        assert raster.units == "unknown"

    def test_validate_schema(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValueError):
            RasterCovariate(
                name="test",
                description="desc",
                source="src",
                path="/fake.tif",
                crs=3857,
                resolution=30.0
            )
            # Note: __init__ calls validate_schema, so if it passes here,
            # it means required fields are present. If 'name' was missing, it would fail.
            pass

    def test_validate_file_exists(self, tmp_path):
        """Test file existence check."""
        fake_path = tmp_path / "fake.tif"
        raster = RasterCovariate(
            name="test",
            description="desc",
            source="src",
            path=str(fake_path),
            crs=3857,
            resolution=30.0
        )
        assert not raster.validate_file_exists()
        
        fake_path.touch()
        assert raster.validate_file_exists()

    def test_units_default(self):
        """Test default units."""
        raster = RasterCovariate(
            name="test",
            description="desc",
            source="src",
            path="/fake.tif",
            crs=3857,
            resolution=30.0
        )
        assert raster.units == "unknown"


class TestTemperatureRaster:
    """Tests for TemperatureRaster model."""

    def test_init_valid_kelvin(self):
        """Test initialization with Kelvin units."""
        temp = TemperatureRaster(
            name="LST_TEST",
            description="Test LST",
            source="MODIS",
            path="/fake.tif",
            crs=3857,
            resolution=30.0,
            units="K"
        )
        assert temp.units == "K"
        assert temp.name == "LST_TEST"

    def test_init_invalid_units(self):
        """Test initialization fails with invalid units."""
        with pytest.raises(ValueError) as exc_info:
            TemperatureRaster(
                name="LST_TEST",
                description="Test LST",
                source="MODIS",
                path="/fake.tif",
                crs=3857,
                resolution=30.0,
                units="FAKE"
            )
        assert "Invalid temperature units" in str(exc_info.value)

    def test_is_valid_temperature_kelvin(self):
        """Test temperature validity check for Kelvin."""
        temp = TemperatureRaster(
            name="LST_TEST",
            description="Test LST",
            source="MODIS",
            path="/fake.tif",
            crs=3857,
            resolution=30.0,
            units="K",
            nodata_value=-9999.0
        )
        assert temp.is_valid_temperature(280.0) # Valid
        assert not temp.is_valid_temperature(-9999.0) # Nodata
        assert not temp.is_valid_temperature(100.0) # Too cold (physically)
        assert not temp.is_valid_temperature(400.0) # Too hot

    def test_is_valid_temperature_celsius(self):
        """Test temperature validity check for Celsius."""
        temp = TemperatureRaster(
            name="LST_TEST",
            description="Test LST",
            source="MODIS",
            path="/fake.tif",
            crs=3857,
            resolution=30.0,
            units="C",
            nodata_value=-9999.0
        )
        assert temp.is_valid_temperature(20.0) # Valid
        assert not temp.is_valid_temperature(-9999.0) # Nodata
        assert not temp.is_valid_temperature(-100.0) # Too cold
        assert not temp.is_valid_temperature(100.0) # Too hot
