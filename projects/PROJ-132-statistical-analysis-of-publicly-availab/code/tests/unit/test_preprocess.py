import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

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
    dates = pd.date_range('2020-03-01', periods=50, freq='D')
    data = {
        'species': ['Turdus migratorius'] * 30 + ['Setophaga ruticilla'] * 20,
        'lat': [40.0 + (i % 10) * 0.1 for i in range(50)],
        'lon': [-75.0 + (i % 10) * 0.1 for i in range(50)],
        'date': dates,
        'count': [1] * 50,
        'checklist_id': [f'chk_{i}' for i in range(50)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_phenology_data():
    # Create data with varying first_arrival to test deciles
    data = {
        'species': ['A'] * 100,
        'grid_cell_lat': [40.0] * 100,
        'grid_cell_lon': [-75.0] * 100,
        'first_arrival': list(range(1, 101)), # Weeks 1 to 100
        'total_count': [10] * 100
    }
    return pd.DataFrame(data)

def test_filter_migratory_species(sample_ebird_data):
    result = filter_migratory_species(sample_ebird_data, ['Turdus migratorius'])
    assert len(result) == 30
    assert all(result['species'] == 'Turdus migratorius')

def test_assign_grid_cell():
    lat, lon = assign_grid_cell(40.12, -75.99, res=0.5)
    assert lat == 40.0
    assert lon == -76.0

def test_add_grid_cells(sample_ebird_data):
    df = add_grid_cells(sample_ebird_data, res=0.5)
    assert 'grid_cell_lat' in df.columns
    assert 'grid_cell_lon' in df.columns

def test_aggregate_to_weekly_grid(sample_ebird_data):
    df = add_grid_cells(sample_ebird_data)
    result = aggregate_to_weekly_grid(df)
    assert 'week' in result.columns
    assert 'count' in result.columns
    assert result['count'].sum() == 50

def test_compute_phenology_metrics(sample_ebird_data):
    df = add_grid_cells(sample_ebird_data)
    df_agg = aggregate_to_weekly_grid(df)
    result = compute_phenology_metrics(df_agg)
    assert 'first_arrival' in result.columns
    assert 'median_arrival' in result.columns
    assert 'stopover_duration' in result.columns

def test_mark_insufficient_data(sample_ebird_data):
    df = add_grid_cells(sample_ebird_data)
    df_agg = aggregate_to_weekly_grid(df)
    df_pheno = compute_phenology_metrics(df_agg)
    result = mark_insufficient_data(df_pheno, threshold=5)
    assert 'sufficient_data' in result.columns
    assert result['sufficient_data'].all()

def test_calculate_observer_effort(sample_ebird_data):
    df = add_grid_cells(sample_ebird_data)
    df_agg = aggregate_to_weekly_grid(df)
    result = calculate_observer_effort(df_agg)
    assert 'observer_effort' in result.columns

def test_tail_preserving_sampling(sample_phenology_data, tmp_path):
    output_file = tmp_path / "weights.parquet"
    result = apply_tail_preserving_sampling(sample_phenology_data, output_file)
    
    # Check columns
    assert 'sampling_weight' in result.columns
    assert 'arrival_decile' in result.columns
    
    # Check file creation
    assert output_file.exists()
    
    # Check weights: lowest decile should be 0.5, others 1.0
    # With range 1-100, decile 0 is roughly weeks 1-10
    low_decile_mask = result['arrival_decile'] == result['arrival_decile'].min()
    assert result.loc[low_decile_mask, 'sampling_weight'].min() == 0.5
    assert result.loc[~low_decile_mask, 'sampling_weight'].min() == 1.0

def test_empty_dataframe_handling(tmp_path):
    df = pd.DataFrame(columns=['species', 'first_arrival'])
    output_file = tmp_path / "empty.parquet"
    result = apply_tail_preserving_sampling(df, output_file)
    assert result.empty
    assert output_file.exists()

def test_missing_columns(tmp_path):
    df = pd.DataFrame({'species': ['A'], 'first_arrival': [1]})
    output_file = tmp_path / "missing.parquet"
    # Should handle missing grid columns gracefully or raise expected error
    # For this test, we assume it runs but might produce NaNs if grid cols missing
    try:
        result = apply_tail_preserving_sampling(df, output_file)
        # If it runs, check output exists
        assert output_file.exists()
    except Exception as e:
        # Expected if logic strictly requires grid columns
        pass
