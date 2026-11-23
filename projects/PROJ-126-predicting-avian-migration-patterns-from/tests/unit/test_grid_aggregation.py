"""
Unit tests for grid aggregation logic in preprocessing.py.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

from preprocessing import _clip_to_lake_powell, _aggregate_to_grid, join_environmental_data
from config import LAKE_POWELL_BOUNDS

@pytest.fixture
def sample_ebird_df():
    """Create a sample eBird DataFrame with points inside and outside Lake Powell."""
    # Lake Powell bounds approx: lat 36.8-37.3, lon -111.8 to -110.5
    data = {
        'latitude': [37.0, 37.1, 36.5, 38.0, 37.2],  # 3 inside, 2 outside
        'longitude': [-111.0, -111.2, -111.5, -110.0, -111.0],
        'count': [1, 2, 3, 4, 5],
        'date': pd.to_datetime(['2020-05-01', '2020-05-08', '2020-05-01', '2020-05-01', '2020-05-01'])
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_modis_df():
    """Create a sample MODIS DataFrame."""
    data = {
        'grid_id': ['R37C-111', 'R37C-112'],
        'week': ['20', '20'],
        'temp_mean': [20.5, 21.0],
        'ndvi_mean': [0.4, 0.5]
    }
    return pd.DataFrame(data)

def test_clip_to_lake_powell_in_bounds(sample_ebird_df):
    """Test that points within bounds are kept."""
    result = _clip_to_lake_powell(sample_ebird_df)
    # Expected: 3 points (indices 0, 1, 4)
    # Index 2 (36.5) is below min_lat (36.8)
    # Index 3 (38.0) is above max_lat (37.3)
    assert len(result) == 3
    assert all(result['latitude'] >= LAKE_POWELL_BOUNDS['lat_min'])
    assert all(result['latitude'] <= LAKE_POWELL_BOUNDS['lat_max'])

def test_aggregate_to_grid(sample_ebird_df):
    """Test grid aggregation logic."""
    clipped = _clip_to_lake_powell(sample_ebird_df)
    result = _aggregate_to_grid(clipped)
    
    assert 'grid_id' in result.columns
    assert 'count' in result.columns
    assert 'week' in result.columns
    # Counts should be summed
    assert result['count'].sum() == clipped['count'].sum()

def test_join_environmental_data(sample_ebird_df, sample_modis_df):
    """Test joining eBird counts with MODIS data."""
    clipped = _clip_to_lake_powell(sample_ebird_df)
    grid_counts = _aggregate_to_grid(clipped)
    
    # Manually adjust grid_ids in sample_modis to match aggregated ones if needed
    # For this test, we assume the aggregation produces IDs that match or overlap
    # In reality, grid_ids depend on floor division of lat/lon
    
    # Create a mock grid_counts with a known grid_id that matches sample_modis
    mock_grid = pd.DataFrame({
        'grid_id': ['R37C-111'],
        'week': ['20'],
        'count': [10],
        'grid_row': [37],
        'grid_col': [-111]
    })
    
    result = join_environmental_data(mock_grid, sample_modis_df)
    
    assert 'temp_mean' in result.columns
    assert 'ndvi_mean' in result.columns
    assert 'env_missing' in result.columns
    assert result['env_missing'].sum() == 0  # No missing data in this case

def test_join_missing_environmental_data():
    """Test that missing environmental data is flagged."""
    grid_counts = pd.DataFrame({
        'grid_id': ['R99C99'],
        'week': ['99'],
        'count': [5],
        'grid_row': [99],
        'grid_col': [99]
    })
    
    modis_df = pd.DataFrame({
        'grid_id': ['R37C-111'],
        'week': ['20'],
        'temp_mean': [20.0],
        'ndvi_mean': [0.4]
    })
    
    result = join_environmental_data(grid_counts, modis_df)
    
    assert result['env_missing'].iloc[0] is True