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
        'species': ['Turdus migratorius', 'Setophaga ruticilla', 'Cardinalis cardinalis',
                   'Turdus migratorius', 'Setophaga ruticilla'],
        'lat': [40.7, 40.8, 40.9, 41.0, 41.1],
        'lon': [-74.0, -74.1, -74.2, -74.3, -74.4],
        'date': ['2023-03-01', '2023-03-05', '2023-03-10', '2023-03-15', '2023-03-20'],
        'count': [5, 3, 8, 2, 4],
        'checklist_id': ['chk_001', 'chk_002', 'chk_003', 'chk_004', 'chk_005']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_phenology_data():
    """Create sample phenology data for testing."""
    data = {
        'species': ['Turdus migratorius', 'Turdus migratorius', 'Setophaga ruticilla'],
        'grid_cell': ['40.5_-74.0', '40.5_-74.0', '40.5_-74.0'],
        'week': [10, 11, 10],
        'phenology_metric': ['first_arrival', 'median_arrival', 'first_arrival'],
        'value': [10, 11, 10]
    }
    return pd.DataFrame(data)

def test_filter_migratory_species(sample_ebird_data):
    """Test filtering to migratory species."""
    clo_list = ['Turdus migratorius', 'Setophaga ruticilla']
    filtered = filter_migratory_species(sample_ebird_data, clo_list)
    
    assert len(filtered) == 4  # Should keep 4 out of 5 records
    assert 'Cardinalis cardinalis' not in filtered['species'].values

def test_assign_grid_cell():
    """Test grid cell assignment."""
    grid_lat, grid_lon = assign_grid_cell(40.7, -74.0, grid_res=0.5)
    assert grid_lat == 40.5
    assert grid_lon == -74.0

    grid_lat, grid_lon = assign_grid_cell(40.8, -74.1, grid_res=0.5)
    assert grid_lat == 41.0
    assert grid_lon == -74.0

def test_add_grid_cells(sample_ebird_data):
    """Test adding grid cells to DataFrame."""
    df = add_grid_cells(sample_ebird_data, grid_res=0.5)
    
    assert 'grid_cell' in df.columns
    assert 'grid_lat' in df.columns
    assert 'grid_lon' in df.columns
    
    # Check first row
    assert df.iloc[0]['grid_cell'] == '40.5_-74.0'

def test_aggregate_to_weekly_grid(sample_ebird_data):
    """Test aggregation to weekly grid."""
    df = add_grid_cells(sample_ebird_data, grid_res=0.5)
    aggregated = aggregate_to_weekly_grid(df)
    
    assert 'week' in aggregated.columns
    assert 'year' in aggregated.columns
    assert 'count' in aggregated.columns
    assert 'num_checklists' in aggregated.columns

def test_compute_phenology_metrics(sample_ebird_data):
    """Test phenology metric computation."""
    df = add_grid_cells(sample_ebird_data, grid_res=0.5)
    aggregated = aggregate_to_weekly_grid(df)
    phenology = compute_phenology_metrics(aggregated)
    
    if not phenology.empty:
        assert 'phenology_metric' in phenology.columns
        assert 'value' in phenology.columns
        assert 'first_arrival' in phenology['phenology_metric'].values

def test_mark_insufficient_data(sample_ebird_data):
    """Test marking insufficient data."""
    df = add_grid_cells(sample_ebird_data, grid_res=0.5)
    aggregated = aggregate_to_weekly_grid(df)
    marked = mark_insufficient_data(aggregated, min_checklists=2)
    
    assert 'sufficient' in marked.columns
    # All samples have 1 checklist, so with min_checklists=2, all should be False
    assert all(marked['sufficient'] == False)

def test_calculate_observer_effort(sample_ebird_data):
    """Test observer effort calculation."""
    df = add_grid_cells(sample_ebird_data, grid_res=0.5)
    aggregated = aggregate_to_weekly_grid(df)
    effort_df = calculate_observer_effort(aggregated)
    
    assert 'observer_effort' in effort_df.columns
    assert effort_df['observer_effort'].min() >= 0
    assert effort_df['observer_effort'].max() <= 1

def test_tail_preserving_sampling(sample_phenology_data):
    """Test tail-preserving stratified sampling."""
    sampled_df, weights_df = apply_tail_preserving_sampling(sample_phenology_data)
    
    assert 'sampling_weight' in sampled_df.columns
    assert len(weights_df) > 0
    assert 'sampling_weight' in weights_df.columns
    
    # Check that weights are either 0.5 or 1.0
    unique_weights = weights_df['sampling_weight'].unique()
    assert all(w in [0.5, 1.0] for w in unique_weights)

def test_empty_dataframe_handling():
    """Test handling of empty DataFrames."""
    empty_df = pd.DataFrame(columns=['species', 'lat', 'lon', 'date', 'count', 'checklist_id'])
    
    filtered = filter_migratory_species(empty_df)
    assert len(filtered) == 0
    
    effort_df = calculate_observer_effort(empty_df)
    assert len(effort_df) == 0
    assert 'observer_effort' in effort_df.columns

def test_missing_columns():
    """Test handling of missing required columns."""
    incomplete_df = pd.DataFrame({'species': ['A'], 'lat': [40.0]})
    
    with pytest.raises(ValueError):
        add_grid_cells(incomplete_df)
    
    with pytest.raises(ValueError):
        aggregate_to_weekly_grid(incomplete_df)
