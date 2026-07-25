import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocess import (
    filter_migratory_species,
    assign_grid_cell,
    add_grid_cells,
    aggregate_to_weekly_grid,
    compute_phenology_metrics,
    mark_insufficient_data,
    calculate_observer_effort,
    apply_tail_preserving_sampling
)

@pytest.fixture
def sample_ebird_data():
    """Create sample eBird data for testing."""
    data = {
        'species': ['Turdus migratorius', 'Turdus migratorius', 'Setophaga ruticilla', 
                   'Hirundo rustica', 'Turdus migratorius'],
        'lat': [40.7128, 40.8000, 41.0000, 40.5000, 40.7500],
        'lon': [-74.0060, -73.9000, -74.1000, -74.2000, -73.9500],
        'date': ['2023-03-01', '2023-03-08', '2023-03-15', '2023-03-22', '2023-03-29'],
        'count': [5, 3, 2, 1, 4],
        'checklist_id': ['CHK001', 'CHK002', 'CHK003', 'CHK004', 'CHK005'],
        'observer_id': ['OBS001', 'OBS001', 'OBS002', 'OBS003', 'OBS004']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_phenology_data():
    """Create sample phenology data for testing."""
    data = {
        'species': ['Turdus migratorius', 'Turdus migratorius', 'Setophaga ruticilla'],
        'grid_cell': ['40.5_-74.0', '40.5_-74.0', '41.0_-74.1'],
        'week': [10, 11, 12],
        'first_arrival': [10, 10, 12],
        'median_arrival': [10, 10, 12],
        'stopover_duration': [3, 3, 2]
    }
    return pd.DataFrame(data)

def test_filter_migratory_species(sample_ebird_data):
    """Test filtering to migratory species."""
    clo_list = ['Turdus migratorius', 'Setophaga ruticilla']
    result = filter_migratory_species(sample_ebird_data, clo_list)
    
    assert len(result) == 3  # Should filter out Hirundo rustica
    assert all(result['species'].isin(clo_list))

def test_assign_grid_cell():
    """Test grid cell assignment."""
    lat, lon = assign_grid_cell(40.7128, -74.0060, resolution=0.5)
    assert lat == 40.5
    assert lon == -74.5

def test_add_grid_cells(sample_ebird_data):
    """Test adding grid cells to dataframe."""
    result = add_grid_cells(sample_ebird_data, resolution=0.5)
    
    assert 'grid_cell' in result.columns
    assert 'grid_lat' in result.columns
    assert 'grid_lon' in result.columns
    assert len(result) == len(sample_ebird_data)

def test_aggregate_to_weekly_grid(sample_ebird_data):
    """Test aggregation to weekly grid counts."""
    # First add grid cells
    df_with_grids = add_grid_cells(sample_ebird_data, resolution=0.5)
    result = aggregate_to_weekly_grid(df_with_grids)
    
    assert 'week' in result.columns
    assert 'count' in result.columns
    assert 'grid_cell' in result.columns

def test_compute_phenology_metrics(sample_ebird_data):
    """Test phenology metric computation."""
    # First aggregate to weekly
    df_with_grids = add_grid_cells(sample_ebird_data, resolution=0.5)
    weekly = aggregate_to_weekly_grid(df_with_grids)
    result = compute_phenology_metrics(weekly)
    
    assert 'first_arrival' in result.columns
    assert 'median_arrival' in result.columns
    assert 'stopover_duration' in result.columns

def test_mark_insufficient_data(sample_phenology_data):
    """Test marking insufficient data."""
    result = mark_insufficient_data(sample_phenology_data, min_observations=2)
    
    assert 'insufficient_data' in result.columns
    # All cells have 1 observation, so all should be marked insufficient
    assert all(result['insufficient_data'] == True)

def test_calculate_observer_effort(sample_ebird_data):
    """Test observer effort calculation."""
    result = calculate_observer_effort(sample_ebird_data)
    
    assert 'effort_score' in result.columns
    assert 'checklist_count' in result.columns
    assert all(result['effort_score'] > 0)

def test_tail_preserving_sampling(sample_phenology_data):
    """Test tail-preserving stratified sampling."""
    result = apply_tail_preserving_sampling(sample_phenology_data)
    
    assert 'sampling_weight' in result.columns
    assert 'arrival_decile' in result.columns
    # Weights should be either 0.5 or 1.0
    assert all(result['sampling_weight'].isin([0.5, 1.0]))

def test_empty_dataframe_handling():
    """Test handling of empty dataframes."""
    empty_df = pd.DataFrame(columns=['species', 'lat', 'lon', 'date', 'count'])
    
    # Test various functions with empty dataframe
    result = filter_migratory_species(empty_df)
    assert len(result) == 0
    
    result = add_grid_cells(empty_df)
    assert len(result) == 0
    
    result = calculate_observer_effort(empty_df)
    assert len(result) == 0

def test_missing_columns():
    """Test handling of dataframes with missing columns."""
    incomplete_df = pd.DataFrame({'species': ['Turdus migratorius']})
    
    # Should handle gracefully
    result = filter_migratory_species(incomplete_df)
    assert len(result) == 0  # No valid species data

def test_mark_insufficient_data_edge_cases():
    """Test edge cases for insufficient data marking."""
    # Single observation
    single_df = pd.DataFrame({
        'species': ['Turdus migratorius'],
        'grid_cell': ['40.5_-74.0'],
        'week': [10],
        'first_arrival': [10]
    })
    
    result = mark_insufficient_data(single_df, min_observations=5)
    assert result['insufficient_data'].iloc[0] == True
    
    # Multiple observations meeting threshold
    multiple_df = pd.DataFrame({
        'species': ['Turdus migratorius'] * 10,
        'grid_cell': ['40.5_-74.0'] * 10,
        'week': list(range(10, 20)),
        'first_arrival': [10] * 10
    })
    
    result = mark_insufficient_data(multiple_df, min_observations=5)
    assert result['insufficient_data'].iloc[0] == False