import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.data.preprocess import run_preprocessing_pipeline
from src.lib.config import Config

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_run_preprocessing_pipeline_with_synthetic_data(temp_data_dir):
    """Test the full preprocessing pipeline with synthetic data."""
    # Create synthetic eBird data
    ebird_data = {
        'species': ['American Robin', 'American Robin', 'Gray Catbird', 'Black-capped Chickadee'] * 10,
        'lat': [40.0 + np.random.rand() * 0.5 for _ in range(40)],
        'lon': [-75.0 + np.random.rand() * 0.5 for _ in range(40)],
        'date': [datetime(2023, 3, 1) + pd.Timedelta(days=np.random.randint(0, 30)) for _ in range(40)],
        'count': np.random.randint(1, 20, 40),
        'checklist_id': [f'CL_{i}' for i in range(40)]
    }
    ebird_df = pd.DataFrame(ebird_data)
    
    ebird_path = temp_data_dir / 'ebird.csv'
    ebird_df.to_csv(ebird_path, index=False)
    
    # Create dummy climate data
    climate_data = {
        'lat': [40.0, 40.5],
        'lon': [-75.0, -75.5],
        'temp': [10.0, 12.0],
        'week': [1, 2],
        'precip': [5.0, 3.0]
    }
    climate_df = pd.DataFrame(climate_data)
    climate_path = temp_data_dir / 'climate.parquet'
    climate_df.to_parquet(climate_path)
    
    # Run pipeline
    output_path = temp_data_dir / 'processed.parquet'
    config = Config()
    
    result_df = run_preprocessing_pipeline(
        raw_ebird_path=ebird_path,
        raw_climate_path=climate_path,
        output_path=output_path,
        config=config,
        min_observations=3
    )
    
    # Verify output
    assert output_path.exists()
    assert 'data_quality' in result_df.columns
    assert result_df['data_quality'].isin(['sufficient', 'insufficient']).all()
    assert 'observer_effort' in result_df.columns
    assert 'first_arrival' in result_df.columns

def test_preprocessing_output_schema(temp_data_dir):
    """Test that preprocessing output has the expected schema."""
    # Create minimal synthetic data
    ebird_data = {
        'species': ['American Robin'] * 10,
        'lat': [40.0] * 10,
        'lon': [-75.0] * 10,
        'date': [datetime(2023, 3, 1) + pd.Timedelta(days=i) for i in range(10)],
        'count': [5] * 10,
        'checklist_id': [f'CL_{i}' for i in range(10)]
    }
    ebird_df = pd.DataFrame(ebird_data)
    
    ebird_path = temp_data_dir / 'ebird.csv'
    ebird_df.to_csv(ebird_path, index=False)
    
    climate_data = {
        'lat': [40.0],
        'lon': [-75.0],
        'temp': [10.0],
        'week': [1],
        'precip': [5.0]
    }
    climate_df = pd.DataFrame(climate_data)
    climate_path = temp_data_dir / 'climate.parquet'
    climate_df.to_parquet(climate_path)
    
    output_path = temp_data_dir / 'processed.parquet'
    config = Config()
    
    result_df = run_preprocessing_pipeline(
        raw_ebird_path=ebird_path,
        raw_climate_path=climate_path,
        output_path=output_path,
        config=config,
        min_observations=5
    )
    
    # Check required columns
    required_columns = [
        'species', 'grid_cell', 'week', 'phenology_metric', 
        'climate_temp_avg', 'climate_precip_total', 
        'data_quality', 'observer_effort'
    ]
    
    # Note: Some columns might be added by other pipeline steps (T017b)
    # We check for the key columns added by T018
    assert 'data_quality' in result_df.columns
    assert 'observer_effort' in result_df.columns
    assert 'grid_cell' in result_df.columns
    assert 'week' in result_df.columns