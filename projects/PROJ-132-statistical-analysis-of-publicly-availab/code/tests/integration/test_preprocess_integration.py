import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.preprocess import (
    run_preprocessing_pipeline,
    mark_insufficient_data
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_ebird_data(temp_data_dir):
    """Create sample eBird data file."""
    data = {
        'species': ['Turdus migratorius', 'Turdus migratorius', 'Turdus migratorius', 
                   'Setophaga coronata', 'Setophaga coronata', 'Turdus migratorius',
                   'Turdus migratorius'],  # Low count for insufficient test
        'lat': [40.1, 40.2, 40.15, 40.3, 40.25, 40.1, 40.1],
        'lon': [-74.0, -74.1, -74.05, -74.2, -74.15, -74.0, -74.0],
        'date': ['2023-03-01', '2023-03-08', '2023-03-15', '2023-03-01', '2023-03-08', 
                '2023-03-01', '2023-03-02'],
        'count': [5, 3, 2, 10, 8, 1, 1],  # Last one has low count
        'checklist_id': ['chk1', 'chk2', 'chk3', 'chk4', 'chk5', 'chk1', 'chk6']
    }
    df = pd.DataFrame(data)
    ebird_path = Path(temp_data_dir) / "ebird_sample.parquet"
    df.to_parquet(ebird_path)
    return str(ebird_path)

@pytest.fixture
def sample_climate_data(temp_data_dir):
    """Create sample climate data file."""
    data = {
        'lat': [40.0, 40.5, 41.0],
        'lon': [-74.0, -74.5, -75.0],
        'temp': [10.5, 12.3, 8.7],
        'week': [9, 10, 11],
        'precip': [5.2, 3.1, 7.8]
    }
    df = pd.DataFrame(data)
    climate_path = Path(temp_data_dir) / "climate_sample.parquet"
    df.to_parquet(climate_path)
    return str(climate_path)

@pytest.fixture
def sample_state_file(temp_data_dir):
    """Create sample state file."""
    import yaml
    state = {
        'artifact_hashes': {
            'ebird': 'abc123',
            'climate': 'def456'
        },
        'updated_at': '2023-01-01'
    }
    state_path = Path(temp_data_dir) / "state.yaml"
    with open(state_path, 'w') as f:
        yaml.dump(state, f)
    return str(state_path)

def test_run_preprocessing_pipeline_with_synthetic_data(
    temp_data_dir,
    sample_ebird_data,
    sample_climate_data,
    sample_state_file
):
    """Test full preprocessing pipeline with synthetic data."""
    output_dir = Path(temp_data_dir) / "output"
    
    result = run_preprocessing_pipeline(
        ebird_path=sample_ebird_data,
        climate_path=sample_climate_data,
        output_dir=str(output_dir),
        state_file=sample_state_file,
        clo_list=['Turdus migratorius', 'Setophaga coronata']
    )
    
    assert 'phenology_file' in result
    assert os.path.exists(result['phenology_file'])
    assert result['total_records'] > 0
    assert 'sufficient_records' in result
    assert 'insufficient_records' in result

def test_preprocessing_output_schema(
    temp_data_dir,
    sample_ebird_data,
    sample_climate_data,
    sample_state_file
):
    """Test that preprocessing output has correct schema."""
    output_dir = Path(temp_data_dir) / "output"
    
    result = run_preprocessing_pipeline(
        ebird_path=sample_ebird_data,
        climate_path=sample_climate_data,
        output_dir=str(output_dir),
        state_file=sample_state_file,
        clo_list=['Turdus migratorius', 'Setophaga coronata']
    )
    
    df = pd.read_parquet(result['phenology_file'])
    
    expected_columns = [
        'species', 'grid_cell', 'year', 'first_arrival', 'median_arrival',
        'stopover_duration', 'total_count', 'sufficient_data', 'observer_effort',
        'normalized_effort', 'sampling_weight'
    ]
    
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"

def test_mark_insufficient_data_integration(
    temp_data_dir,
    sample_ebird_data,
    sample_climate_data,
    sample_state_file
):
    """Test that insufficient data marking works in pipeline."""
    output_dir = Path(temp_data_dir) / "output"
    
    result = run_preprocessing_pipeline(
        ebird_path=sample_ebird_data,
        climate_path=sample_climate_data,
        output_dir=str(output_dir),
        state_file=sample_state_file,
        clo_list=['Turdus migratorius', 'Setophaga coronata']
    )
    
    df = pd.read_parquet(result['phenology_file'])
    
    # Check that sufficient_data column exists and has boolean values
    assert 'sufficient_data' in df.columns
    assert df['sufficient_data'].dtype == bool
    
    # Verify that at least some records are marked as sufficient
    assert df['sufficient_data'].sum() > 0
    
    # Verify that insufficient records are properly flagged
    insufficient_df = df[~df['sufficient_data']]
    if len(insufficient_df) > 0:
        # Check that insufficient records have low counts or checklists
        for _, row in insufficient_df.iterrows():
            assert row['total_count'] < 10 or row['observer_effort'] < 5
