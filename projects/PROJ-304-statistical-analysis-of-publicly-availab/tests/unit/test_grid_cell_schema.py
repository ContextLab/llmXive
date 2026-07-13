"""
Unit tests for the SpatialGridCell schema.
"""
import pytest
from datetime import date
from shapely.geometry import Point, Polygon, mapping
from code.schemas.grid_cell import SpatialGridCell


def test_create_spatial_grid_cell_with_shapely():
    """Test creating a cell with a Shapely geometry object."""
    geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    cell = SpatialGridCell(
        grid_id="cell_001",
        geometry=geom,
        noise_metrics={"mean": 55.0, "max": 70.0},
        covariates={"traffic": 1200.0},
        date=date(2023, 10, 1)
    )
    assert cell.grid_id == "cell_001"
    assert isinstance(cell.geometry, Polygon)
    assert cell.noise_metrics["mean"] == 55.0
    assert cell.date == date(2023, 10, 1)


def test_create_spatial_grid_cell_with_geojson():
    """Test creating a cell with a GeoJSON-like dict."""
    geojson_geom = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
    }
    cell = SpatialGridCell(
        grid_id="cell_002",
        geometry=geojson_geom,
        noise_metrics={"mean": 60.0},
        covariates={},
        date=date(2023, 10, 2)
    )
    assert cell.grid_id == "cell_002"
    assert isinstance(cell.geometry, Polygon)


def test_to_geojson():
    """Test conversion to GeoJSON format."""
    geom = Point(0.5, 0.5)
    cell = SpatialGridCell(
        grid_id="cell_003",
        geometry=geom,
        noise_metrics={"max": 80.0},
        covariates={"population": 5000},
        date=date(2023, 10, 3)
    )
    feature = cell.to_geojson()
    assert feature["type"] == "Feature"
    assert feature["properties"]["grid_id"] == "cell_003"
    assert feature["properties"]["date"] == "2023-10-03"
    assert "geometry" in feature


def test_from_geojson_feature():
    """Test construction from a GeoJSON Feature."""
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [0.5, 0.5]
        },
        "properties": {
            "grid_id": "cell_004",
            "noise_metrics": {"min": 40.0},
            "covariates": {"land_use": "residential"},
            "date": "2023-10-04"
        }
    }
    cell = SpatialGridCell.from_geojson_feature(feature)
    assert cell.grid_id == "cell_004"
    assert cell.date == date(2023, 10, 4)
    assert cell.noise_metrics["min"] == 40.0


def test_invalid_geometry_type():
    """Test that invalid geometry types raise an error."""
    with pytest.raises(TypeError):
        SpatialGridCell(
            grid_id="cell_bad",
            geometry="not a geometry",
            noise_metrics={},
            covariates={},
            date=date.today()
        )