import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import apply_ocean_mask, load_land_mask, get_interim_path

def test_apply_ocean_mask_land_events():
    """Test that events near land are retained."""
    # Create a simple land polygon (a square)
    land_poly = Polygon([(-10, -10), (10, -10), (10, 10), (-10, 10)])
    mask_gdf = gpd.GeoDataFrame([{'id': 1, 'geometry': land_poly}], crs="EPSG:4326")
    
    # Create events: one near land, one far
    events = pd.DataFrame({
        'event_id': ['E1', 'E2'],
        'lat': [5.0, 50.0], # E1 near land, E2 far
        'lon': [5.0, 50.0]
    })
    
    result = apply_ocean_mask(events, mask_gdf, reliability_threshold=0.95)
    
    # E1 should be kept, E2 should be excluded
    assert len(result) == 1
    assert result.iloc[0]['event_id'] == 'E1'

def test_apply_ocean_mask_empty_mask():
    """Test behavior with empty land mask."""
    mask_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    events = pd.DataFrame({
        'event_id': ['E1'],
        'lat': [50.0],
        'lon': [50.0]
    })
    
    # Should return all events when mask is empty
    result = apply_ocean_mask(events, mask_gdf)
    assert len(result) == 1

def test_apply_ocean_mask_output_file():
    """Test that output file is written."""
    land_poly = Polygon([(-10, -10), (10, -10), (10, 10), (-10, 10)])
    mask_gdf = gpd.GeoDataFrame([{'id': 1, 'geometry': land_poly}], crs="EPSG:4326")
    
    events = pd.DataFrame({
        'event_id': ['E1', 'E2'],
        'lat': [5.0, 50.0],
        'lon': [5.0, 50.0]
    })
    
    # Ensure output path parent exists
    output_path = get_interim_path() / "masked_events.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = apply_ocean_mask(events, mask_gdf)
    
    assert output_path.exists()
    # Verify content
    df = pd.read_csv(output_path)
    assert len(df) == 1
    assert df.iloc[0]['event_id'] == 'E1'