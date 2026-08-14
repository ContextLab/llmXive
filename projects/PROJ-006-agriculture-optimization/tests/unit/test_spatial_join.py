"""
Unit tests for the spatial_join module.
"""

import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
from pathlib import Path
import tempfile
import os

from src.data.processing.spatial_join import (
    load_household_data,
    load_remote_sensing_data,
    apply_buffer_to_households,
    perform_spatial_join,
    run_spatial_join,
    DEFAULT_BUFFER_DEG
)
from src.utils.io_helpers import FatalError, IntegrityError


@pytest.fixture
def temp_household_csv(tmp_path):
    """Create a temporary household CSV file."""
    data = {
        'household_id': ['HH1', 'HH2', 'HH3'],
        'latitude': [-13.5, -13.6, -13.7],
        'longitude': [34.0, 34.1, 34.2],
        'country': ['Malawi', 'Malawi', 'Tanzania']
    }
    df = pd.DataFrame(data)
    path = tmp_path / "households.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def temp_pixel_csv(tmp_path):
    """Create a temporary pixel CSV file."""
    data = {
        'pixel_id': ['P1', 'P2', 'P3'],
        'min_lat': [-13.6, -13.7, -13.8],
        'max_lat': [-13.4, -13.5, -13.6],
        'min_lon': [33.9, 34.0, 34.1],
        'max_lon': [34.1, 34.2, 34.3]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "pixels.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def temp_output_csv(tmp_path):
    """Return a path for output CSV."""
    return tmp_path / "joined.csv"


def test_load_household_data_valid(temp_household_csv):
    """Test loading valid household data."""
    gdf = load_household_data(temp_household_csv)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 3
    assert 'household_id' in gdf.columns
    assert 'geometry' in gdf.columns
    assert gdf.crs == "EPSG:4326"


def test_load_household_data_missing_file(tmp_path):
    """Test loading from a missing file raises FatalError."""
    with pytest.raises(FatalError):
        load_household_data(tmp_path / "nonexistent.csv")


def test_load_household_data_missing_columns(tmp_path):
    """Test loading data with missing required columns raises FatalError."""
    data = {'household_id': ['HH1'], 'latitude': [-13.5]}
    df = pd.DataFrame(data)
    path = tmp_path / "bad.csv"
    df.to_csv(path, index=False)

    with pytest.raises(FatalError):
        load_household_data(path)


def test_load_remote_sensing_data_valid(temp_pixel_csv):
    """Test loading valid pixel data."""
    gdf = load_remote_sensing_data(temp_pixel_csv)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 3
    assert 'pixel_id' in gdf.columns
    assert 'geometry' in gdf.columns
    # Check that geometry is a box
    for geom in gdf['geometry']:
        assert geom.geom_type == 'Polygon'


def test_load_remote_sensing_data_missing_file(tmp_path):
    """Test loading from a missing file raises FatalError."""
    with pytest.raises(FatalError):
        load_remote_sensing_data(tmp_path / "nonexistent.csv")


def test_apply_buffer_to_households(temp_household_csv):
    """Test buffering household points."""
    gdf = load_household_data(temp_household_csv)
    buffered = apply_buffer_to_households(gdf, buffer_deg=0.05)

    assert len(buffered) == 3
    # Check that geometry is now a polygon (buffered point)
    for geom in buffered['geometry']:
        assert geom.geom_type == 'Polygon'
        # Area should be greater than 0
        assert geom.area > 0


def test_perform_spatial_join_no_overlap(tmp_path):
    """Test spatial join when there is no overlap."""
    # Create households far away from pixels
    h_data = {
        'household_id': ['HH1'],
        'latitude': [0.0],
        'longitude': [0.0]
    }
    h_df = pd.DataFrame(h_data)
    h_path = tmp_path / "h.csv"
    h_df.to_csv(h_path, index=False)

    p_data = {
        'pixel_id': ['P1'],
        'min_lat': [10.0],
        'max_lat': [11.0],
        'min_lon': [10.0],
        'max_lon': [11.0]
    }
    p_df = pd.DataFrame(p_data)
    p_path = tmp_path / "p.csv"
    p_df.to_csv(p_path, index=False)

    h_gdf = load_household_data(h_path)
    h_buffered = apply_buffer_to_households(h_gdf, buffer_deg=0.1) # Still too far
    p_gdf = load_remote_sensing_data(p_path)

    result = perform_spatial_join(h_buffered, p_gdf)
    assert result.empty


def test_run_spatial_join_end_to_end(temp_household_csv, temp_pixel_csv, temp_output_csv):
    """Test the full spatial join pipeline."""
    stats = run_spatial_join(
        household_input=temp_household_csv,
        pixel_input=temp_pixel_csv,
        output_path=temp_output_csv,
        buffer_deg=0.05
    )

    assert temp_output_csv.exists()
    assert stats['matches_found'] > 0
    assert stats['households_processed'] == 3
    assert stats['pixels_processed'] == 3

    # Verify output file content
    result_df = pd.read_csv(temp_output_csv)
    assert 'household_id' in result_df.columns
    assert 'pixel_id' in result_df.columns
    assert len(result_df) == stats['matches_found']


def test_run_spatial_join_no_matches_raises(tmp_path):
    """Test that run_spatial_join raises IntegrityError if no matches found."""
    # Create disjoint data
    h_data = {'household_id': ['HH1'], 'latitude': [0.0], 'longitude': [0.0]}
    h_df = pd.DataFrame(h_data)
    h_path = tmp_path / "h.csv"
    h_df.to_csv(h_path, index=False)

    p_data = {'pixel_id': ['P1'], 'min_lat': [10.0], 'max_lat': [11.0], 'min_lon': [10.0], 'max_lon': [11.0]}
    p_df = pd.DataFrame(p_data)
    p_path = tmp_path / "p.csv"
    p_df.to_csv(p_path, index=False)

    out_path = tmp_path / "out.csv"

    with pytest.raises(IntegrityError):
        run_spatial_join(h_path, p_path, out_path, buffer_deg=0.1)
