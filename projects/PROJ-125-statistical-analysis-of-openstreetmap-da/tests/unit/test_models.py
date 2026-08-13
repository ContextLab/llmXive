"""
Unit tests for data models (CityBoundary, RasterCovariate, TemperatureRaster).
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np

# Import models
from code.models.base import BaseModel
from code.models.city import CityBoundary
from code.models.raster import RasterCovariate, TemperatureRaster
from shapely.geometry import box, Polygon


class TestCityBoundary:
    def test_init_valid_polygon(self):
        poly = box(0, 0, 10, 10)
        city = CityBoundary(city_name="TestCity", geometry=poly, crs="EPSG:4326")
        assert city.city_name == "TestCity"
        assert city.crs == "EPSG:4326"
        assert city.validate() is True

    def test_init_from_geojson_string(self):
        geom_dict = {"type": "Polygon", "coordinates": [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]]}
        city = CityBoundary(city_name="GeoJSONCity", geometry=geom_dict, crs="EPSG:3857")
        assert city.city_name == "GeoJSONCity"
        assert city.validate() is True

    def test_to_dict(self):
        poly = box(0, 0, 10, 10)
        city = CityBoundary(city_name="DictCity", geometry=poly, crs="EPSG:4326")
        d = city.to_dict()
        assert d["type"] == "Feature"
        assert d["properties"]["city_name"] == "DictCity"
        assert "geometry" in d

    def test_validate_invalid_geometry(self):
        # Create an invalid geometry (self-intersecting)
        invalid_poly = Polygon([(0, 0), (10, 0), (5, 5), (5, 10), (0, 10), (10, 10)])
        city = CityBoundary(city_name="BadCity", geometry=invalid_poly, crs="EPSG:4326")
        # Note: Shapely might auto-fix simple issues, but let's test the logic
        # If geometry is actually invalid, validate should return False
        if not invalid_poly.is_valid:
            assert city.validate() is False
        else:
            # If shapely fixed it, we check that the method runs without error
            assert city.validate() is True

    def test_save_and_load(self):
        poly = box(0, 0, 10, 10)
        city = CityBoundary(city_name="SaveCity", geometry=poly, crs="EPSG:4326")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "city.json"
            city.save(path)
            
            assert path.exists()
            
            loaded = CityBoundary.load(path)
            assert loaded.city_name == "SaveCity"
            assert loaded.geometry.equals(city.geometry)


class TestRasterCovariate:
    def test_init(self):
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
            fname = f.name
        try:
            cov = RasterCovariate(name="test_cov", file_path=fname, variable_type="continuous")
            assert cov.name == "test_cov"
            assert cov.validate() is True
        finally:
            os.unlink(fname)

    def test_validate_missing_file(self):
        cov = RasterCovariate(name="missing", file_path="/nonexistent/path.tif")
        assert cov.validate() is False

    def test_validate_invalid_type(self):
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
            fname = f.name
        try:
            cov = RasterCovariate(name="bad_type", file_path=fname, variable_type="invalid")
            assert cov.validate() is False
        finally:
            os.unlink(fname)

    def test_get_stats_no_file(self):
        cov = RasterCovariate(name="no_file", file_path="/nonexistent.tif")
        stats = cov.get_stats()
        assert np.isnan(stats["min"])


class TestTemperatureRaster:
    def test_init(self):
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
            fname = f.name
        try:
            temp = TemperatureRaster(file_path=fname, unit="C", period="2023_summer")
            assert temp.unit == "C"
            assert temp.validate() is True
        finally:
            os.unlink(fname)

    def test_validate_invalid_unit(self):
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
            fname = f.name
        try:
            temp = TemperatureRaster(file_path=fname, unit="F")
            assert temp.validate() is False
        finally:
            os.unlink(fname)

    def test_validate_cloud_cover(self):
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
            fname = f.name
        try:
            temp = TemperatureRaster(file_path=fname, cloud_cover_pct=150.0)
            assert temp.validate() is False
        finally:
            os.unlink(fname)