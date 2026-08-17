"""
Unit tests for data models (CityBoundary, RasterCovariate, TemperatureRaster).
"""
import json
import tempfile
from pathlib import Path
import pytest
from shapely.geometry import Polygon, mapping

from code.models.base import BaseModel
from code.models.city import CityBoundary
from code.models.raster import RasterCovariate, TemperatureRaster


class TestBaseModel:
    def test_to_dict(self):
        class TestModel(BaseModel):
            def __init__(self, a, b):
                self.a = a
                self.b = b
        
        model = TestModel(1, 2)
        assert model.to_dict() == {"a": 1, "b": 2}

    def test_save_and_load(self):
        class TestModel(BaseModel):
            def __init__(self, value):
                self.value = value

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            model = TestModel(42)
            model.save(path)
            
            assert path.exists()
            loaded = TestModel.from_json_file(path)
            assert loaded.value == 42

    def test_validate_schema_missing_field(self):
        with pytest.raises(ValueError, match="Missing required fields"):
            BaseModel.validate_schema({"a": 1}, ["a", "b"])

    def test_validate_schema_valid(self):
        # Should not raise
        BaseModel.validate_schema({"a": 1, "b": 2}, ["a", "b"])


class TestCityBoundary:
    def test_init_valid(self):
        wkt = "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
        city = CityBoundary(
            city_name="TestCity",
            geometry_wkt=wkt,
            crs_epsg=4326,
            country="USA"
        )
        assert city.city_name == "TestCity"
        assert city.crs_epsg == 4326
        assert city.country == "USA"

    def test_init_invalid_wkt(self):
        with pytest.raises(ValueError, match="Failed to parse geometry WKT"):
            CityBoundary(
                city_name="BadCity",
                geometry_wkt="NOT_A_WKT",
                crs_epsg=4326
            )

    def test_init_missing_required(self):
        with pytest.raises(ValueError, match="Missing required fields"):
            CityBoundary(
                city_name=None, # type: ignore
                geometry_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
                crs_epsg=4326
            )

    def test_bounds(self):
        wkt = "POLYGON((0 0, 2 0, 2 2, 0 2, 0 0))"
        city = CityBoundary("City", wkt, 4326)
        bounds = city.bounds
        assert bounds["minx"] == 0.0
        assert bounds["maxx"] == 2.0

    def test_from_geojson_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "city.geojson"
            geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
            feature = {
                "type": "Feature",
                "properties": {"name": "GeoCity", "country": "Test"},
                "geometry": mapping(geom)
            }
            with open(path, "w") as f:
                json.dump(feature, f)
            
            city = CityBoundary.from_geojson_file(path)
            assert city.city_name == "GeoCity"
            assert city.country == "Test"


class TestRasterCovariate:
    def test_init_valid(self):
        raster = RasterCovariate(
            name="test_cov",
            path="/fake/path.tif",
            crs_epsg=3857,
            resolution_m=30.0,
            data_type="continuous"
        )
        assert raster.name == "test_cov"
        assert raster.resolution_m == 30.0

    def test_init_missing_required(self):
        with pytest.raises(ValueError, match="Missing required fields"):
            RasterCovariate(
                name="test",
                path="/fake.tif",
                crs_epsg=3857,
                resolution_m=30.0,
                data_type=None # type: ignore
            )

    def test_from_raster_file_missing(self):
        with pytest.raises(FileNotFoundError):
            RasterCovariate.from_raster_file(Path("/nonexistent.tif"))


class TestTemperatureRaster:
    def test_init_valid(self):
        temp = TemperatureRaster(
            name="lst_2023",
            path="/fake/lst.tif",
            crs_epsg=3857,
            resolution_m=100.0,
            acquisition_time="2023-01-01T12:00:00Z"
        )
        assert temp.name == "lst_2023"
        assert temp.sensor == "MODIS"

    def test_init_missing_required(self):
        with pytest.raises(ValueError, match="Missing required fields"):
            TemperatureRaster(
                name="test",
                path="/fake.tif",
                crs_epsg=3857,
                resolution_m=100.0,
                acquisition_time=None # type: ignore
            )