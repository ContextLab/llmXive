import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import os

from src.data.preprocess import (
    filter_migratory_species,
    assign_grid_cell,
    add_grid_cells,
    aggregate_to_weekly_grid,
    compute_phenology_metrics,
    mark_insufficient_data,
    calculate_observer_effort,
    run_preprocessing_pipeline
)

@pytest.fixture
def sample_ebird_data():
    """Create sample eBird data for testing."""
    data = {
        'species': ['American Robin', 'American Robin', 'Gray Catbird', 'Black-capped Chickadee', 'American Robin'],
        'lat': [40.0, 40.5, 40.0, 40.0, 40.0],
        'lon': [-75.0, -75.0, -75.0, -75.0, -75.0],
        'date': [
            datetime(2023, 3, 1),
            datetime(2023, 3, 8),
            datetime(2023, 3, 1),
            datetime(2023, 3, 15),
            datetime(2023, 3, 1)
        ],
        'count': [5, 10, 3, 2, 0],
        'checklist_id': ['A', 'B', 'C', 'D', 'E']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_phenology_data():
    """Create sample data with phenology metrics already computed."""
    data = {
        'species': ['American Robin', 'American Robin'],
        'grid_cell': ['40.0_-75.0', '40.0_-75.0'],
        'week': [1, 2],
        'count': [5, 10],
        'year': [2023, 2023]
    }
    return pd.DataFrame(data)

def test_filter_migratory_species(sample_ebird_data):
    """Test filtering to migratory species."""
    clo_list = ['American Robin', 'Gray Catbird']
    result = filter_migratory_species(sample_ebird_data, clo_list)
    
    assert len(result) == 3  # Only American Robin and Gray Catbird
    assert all(result['species'].isin(clo_list))

def test_assign_grid_cell():
    """Test grid cell assignment."""
    lat, lon = assign_grid_cell(40.3, -75.2, grid_res=0.5)
    assert lat == 40.0
    assert lon == -75.0

def test_add_grid_cells(sample_ebird_data):
    """Test adding grid cells to DataFrame."""
    result = add_grid_cells(sample_ebird_data, grid_res=0.5)
    
    assert 'grid_cell' in result.columns
    assert len(result) == len(sample_ebird_data)
    assert result['grid_cell'].iloc[0] == '40.0_-75.0'

def test_aggregate_to_weekly_grid(sample_ebird_data):
    """Test aggregation to weekly grid."""
    # Add grid cells first
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)
    result = aggregate_to_weekly_grid(df_with_grid)
    
    assert 'week' in result.columns
    assert 'count' in result.columns
    assert len(result) <= len(df_with_grid)  # Aggregation reduces rows

def test_compute_phenology_metrics(sample_phenology_data):
    """Test phenology metric computation."""
    result = compute_phenology_metrics(sample_phenology_data)
    
    assert 'first_arrival' in result.columns
    assert 'median_arrival' in result.columns
    assert 'stopover_duration' in result.columns
    assert result['first_arrival'].iloc[0] == 1

def test_mark_insufficient_data(sample_ebird_data):
    """Test marking insufficient data."""
    # Add grid cells first
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)
    result = mark_insufficient_data(df_with_grid, min_observations=5)
    
    assert 'data_quality' in result.columns
    assert result['data_quality'].isin(['sufficient', 'insufficient']).all()
    
    # Check that cells with < 5 observations are marked insufficient
    insufficient = result[result['data_quality'] == 'insufficient']
    assert len(insufficient) > 0  # At least some cells should be insufficient

def test_calculate_observer_effort(sample_ebird_data):
    """Test observer effort calculation."""
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)
    result = calculate_observer_effort(df_with_grid)
    
    assert 'observer_effort' in result.columns
    assert result['observer_effort'].iloc[0] >= 1

def test_empty_dataframe_handling():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame(columns=['species', 'lat', 'lon', 'date', 'count', 'checklist_id'])
    
    with pytest.raises(ValueError):
        filter_migratory_species(empty_df, ['American Robin'])

def test_missing_columns():
    """Test error handling for missing columns."""
    df = pd.DataFrame({'species': ['A'], 'lat': [1.0]})
    
    with pytest.raises(ValueError):
        add_grid_cells(df, grid_res=0.5)

def test_mark_insufficient_data_edge_cases():
    """Test edge cases for insufficient data marking."""
    # Create data with exactly min_observations
    data = {
        'species': ['A'] * 5,
        'grid_cell': ['X'] * 5,
        'week': [1, 2, 3, 4, 5],
        'count': [1, 1, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    
    result = mark_insufficient_data(df, min_observations=5)
    assert all(result['data_quality'] == 'sufficient')
    
    # Create data with one less than min_observations
    data = {
        'species': ['A'] * 4,
        'grid_cell': ['X'] * 4,
        'week': [1, 2, 3, 4],
        'count': [1, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    
    result = mark_insufficient_data(df, min_observations=5)
    assert all(result['data_quality'] == 'insufficient')
