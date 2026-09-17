"""
Unit Tests for T017: Spatial Join Module
"""
import pytest
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path
import tempfile
import json

from src.data.processing.spatial_join import apply_geodesic_buffer, verify_linkage_and_trigger_aggregation
from src.utils.io_helpers import write_csv_strict, load_json_strict

@pytest.fixture
def sample_survey_df():
    """Create a sample survey DataFrame with coordinates."""
    data = {
        'household_id': [1, 2, 3, 4, 5],
        'latitude': [-12.5, -12.6, -12.7, -12.8, None], # One missing
        'longitude': [34.5, 34.6, 34.7, 34.8, 34.9],
        'land_size': [1.2, 1.5, 0.8, 2.0, 1.1],
        'education_level': [4, 5, 3, 6, 4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_workspace():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_apply_geodesic_buffer_valid_coords(sample_survey_df):
    """Test that buffer is applied correctly to valid coordinates."""
    gdf = apply_geodesic_buffer(sample_survey_df, 1.0) # 1km buffer
    
    assert len(gdf) == 4, "Should filter out the row with missing coordinates"
    assert 'geometry' in gdf.columns
    assert all(gdf.geometry.type == 'Polygon')
    
    # Check that polygons are not empty
    assert all(gdf.geometry.area > 0)

def test_apply_geodesic_buffer_no_coords():
    """Test behavior when all coordinates are missing."""
    df = pd.DataFrame({
        'household_id': [1, 2],
        'latitude': [None, None],
        'longitude': [None, None]
    })
    gdf = apply_geodesic_buffer(df, 1.0)
    assert len(gdf) == 0

def test_verify_linkage_and_trigger_aggregation_success(sample_survey_df):
    """Test successful linkage case."""
    # Create a joined dataframe with 4 rows (matching valid coords)
    df_joined = sample_survey_df.dropna(subset=['latitude']).copy()
    df_joined['mean_ndvi'] = 0.5
    
    result = verify_linkage_and_trigger_aggregation(sample_survey_df, df_joined, linkage_threshold=0.95, min_households=300)
    
    # Total valid is 4, matched is 4. Percentage = 100%.
    # But N=4 < 300, so triggered_aggregation should be True due to min_households.
    assert result['total_valid_households'] == 4
    assert result['linkage_percentage'] == 100.0
    assert result['triggered_aggregation'] == True
    assert 'min_households' in result['exclusion_reason']

def test_verify_linkage_and_trigger_aggregation_low_linkage():
    """Test case where linkage percentage is low."""
    df_raw = pd.DataFrame({
        'household_id': [1, 2, 3, 4, 5],
        'latitude': [1.0, 2.0, 3.0, 4.0, 5.0],
        'longitude': [1.0, 2.0, 3.0, 4.0, 5.0]
    })
    # Only 1 matched
    df_joined = df_raw.iloc[[0]].copy()
    df_joined['mean_ndvi'] = 0.5
    
    result = verify_linkage_and_trigger_aggregation(df_raw, df_joined, linkage_threshold=0.95, min_households=1)
    
    assert result['linkage_percentage'] == 20.0 # 1/5
    assert result['triggered_aggregation'] == True
    assert 'Linkage percentage' in result['exclusion_reason']

def test_verify_linkage_and_trigger_aggregation_fatal_no_households():
    """Test case with no valid households in raw data."""
    df_raw = pd.DataFrame({
        'household_id': [1, 2],
        'latitude': [None, None],
        'longitude': [None, None]
    })
    df_joined = pd.DataFrame()
    
    result = verify_linkage_and_trigger_aggregation(df_raw, df_joined)
    
    assert result['total_valid_households'] == 0
    assert result['linkage_percentage'] == 0.0
    assert result['triggered_aggregation'] == True
    assert result['exclusion_reason'] == 'FATAL_NO_HOUSEHOLDS'
