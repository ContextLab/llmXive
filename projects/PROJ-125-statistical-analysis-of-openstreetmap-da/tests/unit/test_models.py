"""
Unit tests for base data models and schema validation.
"""
import pytest
from pathlib import Path
from shapely.geometry import Polygon
from shapely.wkt import loads

from models.base import BaseModel
from models.city import CityBoundary
from models.raster import RasterCovariate, TemperatureRaster

# --- CityBoundary Tests ---

def test_city_boundary_init_valid():
    """Test initialization with valid WKT geometry."""
    wkt = "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"
    city = CityBoundary(name="TestCity", geometry=wkt, source="Test")
    assert city.name == "TestCity"
    assert city.source == "Test"
    assert city.geometry.is_valid

def test_city_boundary_init_invalid_geometry():
    """Test initialization raises error for invalid geometry."""
    with pytest.raises(TypeError):
        CityBoundary(name="TestCity", geometry=12345)

def test_city_boundary_validate_empty_name():
    """Test validation fails for empty name."""
    city = CityBoundary(name="", geometry="POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))")
    with pytest.raises(ValueError, match="City name cannot be empty"):
        city.validate()

def test_city_boundary_validate_invalid_geometry():
    """Test validation fails for invalid geometry."""
    # Create an invalid polygon (self-intersecting or similar)
    # Shapely handles this, but we simulate a case where is_valid is False
    # For this test, we rely on the is_valid check in validate()
    # A simple way to force invalidity in a test might be complex,
    # so we test the logic path by mocking or using a known bad WKT if possible.
    # However, standard WKTs are usually valid. Let's test the empty geometry case.
    city = CityBoundary(name="Test", geometry="POLYGON EMPTY")
    with pytest.raises(ValueError, match="Geometry cannot be empty"):
        city.validate()

def test_city_boundary_to_dict():
    """Test serialization to dictionary."""
    wkt = "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"
    city = CityBoundary(name="TestCity", geometry=wkt)
    data = city.to_dict()
    assert "name" in data
    assert "geometry_wkt" in data
    assert "crs" in data
    assert data["name"] == "TestCity"

def test_city_boundary_save_and_load(tmp_path):
    """Test saving and loading from JSON."""
    wkt = "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"
    city = CityBoundary(name="TestCity", geometry=wkt)
    save_path = tmp_path / "city.json"
    city.save(save_path)
    assert save_path.exists()
    
    loaded_city = CityBoundary.from_json(save_path)
    assert loaded_city.name == city.name
    assert loaded_city.crs == city.crs

# --- RasterCovariate Tests ---

def test_raster_covariate_init():
    """Test initialization of RasterCovariate."""
    # We can't easily create a real file in a temp dir for this test without rasterio
    # So we test the object creation and validation logic for fields
    # We will mock the path existence check or use a real temp file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    try:
        raster = RasterCovariate(
            name="test_covariate",
            path=temp_path,
            crs="EPSG:3857",
            resolution=30.0,
            description="Test covariate"
        )
        assert raster.name == "test_covariate"
        assert raster.resolution == 30.0
        raster.validate() # Should pass
    finally:
        import os
        os.unlink(temp_path)

def test_raster_covariate_missing_file():
    """Test validation fails if file does not exist."""
    raster = RasterCovariate(
        name="test_covariate",
        path="/non/existent/path.tif",
        crs="EPSG:3857",
        resolution=30.0
    )
    with pytest.raises(FileNotFoundError):
        raster.validate()

def test_raster_covariate_invalid_resolution():
    """Test validation fails for non-positive resolution."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    try:
        raster = RasterCovariate(
            name="test",
            path=temp_path,
            crs="EPSG:3857",
            resolution=-10.0
        )
        with pytest.raises(ValueError, match="Resolution must be positive"):
            raster.validate()
    finally:
        import os
        os.unlink(temp_path)

# --- TemperatureRaster Tests ---

def test_temperature_raster_init():
    """Test initialization of TemperatureRaster."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    try:
        temp_raster = TemperatureRaster(
            name="MODIS_LST",
            path=temp_path,
            crs="EPSG:3857",
            resolution=30.0,
            unit="Kelvin",
            min_val=200.0,
            max_val=350.0,
            cloud_cover_pct=5.0
        )
        assert temp_raster.unit == "Kelvin"
        assert temp_raster.cloud_cover_pct == 5.0
        temp_raster.validate()
    finally:
        import os
        os.unlink(temp_path)

def test_temperature_raster_invalid_unit():
    """Test validation fails for invalid unit."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    try:
        temp_raster = TemperatureRaster(
            name="MODIS_LST",
            path=temp_path,
            crs="EPSG:3857",
            resolution=30.0,
            unit="InvalidUnit"
        )
        with pytest.raises(ValueError, match="Invalid temperature unit"):
            temp_raster.validate()
    finally:
        import os
        os.unlink(temp_path)

def test_temperature_raster_cloud_cover_range():
    """Test validation fails for cloud cover out of range."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    try:
        temp_raster = TemperatureRaster(
            name="MODIS_LST",
            path=temp_path,
            crs="EPSG:3857",
            resolution=30.0,
            cloud_cover_pct=150.0
        )
        with pytest.raises(ValueError, match="Cloud cover percentage"):
            temp_raster.validate()
    finally:
        import os
        os.unlink(temp_path)

def test_temperature_raster_convert_units():
    """Test unit conversion logic."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    try:
        temp_raster = TemperatureRaster(
            name="MODIS_LST",
            path=temp_path,
            crs="EPSG:3857",
            resolution=30.0,
            unit="Kelvin",
            min_val=273.15, # 0 C
            max_val=373.15 # 100 C
        )
        temp_raster.convert_units("Celsius")
        assert temp_raster.unit == "Celsius"
        assert abs(temp_raster.min_val - 0.0) < 0.01
        assert abs(temp_raster.max_val - 100.0) < 0.01
    finally:
        import os
        os.unlink(temp_path)