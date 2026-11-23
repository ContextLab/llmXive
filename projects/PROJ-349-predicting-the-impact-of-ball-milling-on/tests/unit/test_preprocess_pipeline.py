"""
Unit tests for the preprocessing pipeline.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from src.preprocess.pipeline import (
    calculate_process_duration,
    flag_unstructured_psd,
    preprocess_data,
    run_preprocessing_pipeline,
    PREDICTOR_COLUMNS,
    TARGET_COLUMNS
)
from src.utils.exceptions import MissingTimestampError


@pytest.fixture
def sample_raw_data():
    """Create a sample raw dataset for testing."""
    data = {
        'experiment_id': ['exp1', 'exp2', 'exp3', 'exp4'],
        'source': ['nist', 'materials_project', 'arxiv', 'nist'],
        'material_type': ['steel', 'aluminum', 'steel', 'copper'],
        'milling_speed': [500.0, 600.0, np.nan, 700.0],
        'milling_time': [2.0, 3.0, 4.0, np.nan],
        'ball_to_powder_ratio': [10.0, 15.0, 20.0, 25.0],
        'youngs_modulus': [200.0, 70.0, np.nan, 110.0],
        'density': [7.8, 2.7, 7.9, 8.9],
        'd10': [10.0, 15.0, 20.0, 25.0],
        'd50': [50.0, 60.0, 70.0, 80.0],
        'd90': [100.0, 120.0, 140.0, 160.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_raw_data_missing_duration(sample_raw_data):
    """Sample data without process_duration column."""
    return sample_raw_data.drop(columns=['process_duration'], errors='ignore')

@pytest.fixture
def sample_raw_data_with_duration(sample_raw_data):
    """Sample data with process_duration column."""
    data = sample_raw_data.copy()
    data['process_duration'] = [3600.0, 7200.0, np.nan, 10800.0]
    return data

def test_calculate_process_duration_with_existing_column(sample_raw_data_with_duration):
    """Test process_duration calculation when column already exists."""
    config = {'process_duration_default': 3600}
    result = calculate_process_duration(sample_raw_data_with_duration, config)
    
    assert 'process_duration' in result.columns
    assert not result['process_duration'].isna().any()
    # Check that NaN was imputed
    assert result.loc[2, 'process_duration'] == result['process_duration'].median()

def test_calculate_process_duration_missing_column(sample_raw_data_missing_duration):
    """Test process_duration calculation when column is missing."""
    config = {'process_duration_default': 3600}
    result = calculate_process_duration(sample_raw_data_missing_duration, config)
    
    assert 'process_duration' in result.columns
    assert not result['process_duration'].isna().any()
    # All values should be the default since no timestamps are available
    assert all(result['process_duration'] == 3600)

def test_calculate_process_duration_with_timestamps():
    """Test process_duration calculation from timestamps."""
    data = {
        'experiment_id': ['exp1', 'exp2'],
        'start_timestamp': ['2023-01-01 00:00:00', '2023-01-01 01:00:00'],
        'end_timestamp': ['2023-01-01 02:00:00', '2023-01-01 03:30:00']
    }
    df = pd.DataFrame(data)
    config = {'process_duration_default': 3600}
    
    result = calculate_process_duration(df, config)
    
    assert 'process_duration' in result.columns
    assert result.loc[0, 'process_duration'] == 7200  # 2 hours
    assert result.loc[1, 'process_duration'] == 9000  # 2.5 hours

def test_flag_unstructured_psd():
    """Test flagging of unstructured PSD entries."""
    data = {
        'experiment_id': ['exp1', 'exp2', 'exp3'],
        'source': ['nist', 'arxiv', 'nist'],
        'raw_blob_hash': ['hash1', 'hash2', 'hash3'],
        'd10': [10.0, np.nan, 30.0],
        'd50': [50.0, np.nan, 70.0],
        'd90': [100.0, np.nan, 140.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {'flagged_psd_path': os.path.join(tmpdir, 'flagged_psd.json')}
        flag_unstructured_psd(df, config)
        
        flagged_path = Path(config['flagged_psd_path'])
        assert flagged_path.exists()
        
        with open(flagged_path, 'r') as f:
            flags = json.load(f)
        
        # Only exp2 should be flagged (missing PSD metrics)
        assert len(flags) == 1
        assert '1' in flags  # index of exp2
        assert flags['1']['issue_type'] == 'missing_psd_metrics'

def test_preprocess_data(sample_raw_data):
    """Test the main preprocessing function."""
    config = {'process_duration_default': 3600}
    
    df_processed, pipeline = preprocess_data(sample_raw_data, config)
    
    # Check that all predictor columns are transformed
    assert len(df_processed) == len(sample_raw_data)
    
    # Check that targets are preserved
    for col in TARGET_COLUMNS:
        assert col in df_processed.columns
        assert not df_processed[col].isna().any()
    
    # Check that pipeline is fitted
    assert pipeline is not None

def test_run_preprocessing_pipeline(sample_raw_data):
    """Test the full pipeline from file to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.parquet')
        output_path = os.path.join(tmpdir, 'output.parquet')
        
        # Save input data
        sample_raw_data.to_parquet(input_path)
        
        # Run pipeline
        df_result = run_preprocessing_pipeline(input_path, output_path)
        
        # Check output file exists
        assert Path(output_path).exists()
        
        # Check result
        assert len(df_result) == len(sample_raw_data)
        assert all(col in df_result.columns for col in TARGET_COLUMNS)

def test_preprocess_data_missing_predictors():
    """Test preprocessing with missing predictor values."""
    data = {
        'experiment_id': ['exp1', 'exp2', 'exp3'],
        'material_type': ['steel', 'aluminum', 'steel'],
        'milling_speed': [500.0, np.nan, 700.0],
        'milling_time': [2.0, 3.0, np.nan],
        'ball_to_powder_ratio': [10.0, 15.0, 20.0],
        'youngs_modulus': [np.nan, 70.0, 200.0],
        'density': [7.8, 2.7, 7.9],
        'd10': [10.0, 15.0, 20.0],
        'd50': [50.0, 60.0, 70.0],
        'd90': [100.0, 120.0, 140.0]
    }
    df = pd.DataFrame(data)
    config = {'process_duration_default': 3600}
    
    df_processed, pipeline = preprocess_data(df, config)
    
    # Check that missing values were imputed
    assert not df_processed[PREDICTOR_COLUMNS].isna().any().any()
    assert len(df_processed) == len(df)

def test_preprocess_data_no_categorical():
    """Test preprocessing when no categorical columns exist."""
    data = {
        'experiment_id': ['exp1', 'exp2'],
        'milling_speed': [500.0, 600.0],
        'milling_time': [2.0, 3.0],
        'ball_to_powder_ratio': [10.0, 15.0],
        'youngs_modulus': [200.0, 70.0],
        'density': [7.8, 2.7],
        'd10': [10.0, 15.0],
        'd50': [50.0, 60.0],
        'd90': [100.0, 120.0]
    }
    df = pd.DataFrame(data)
    config = {'process_duration_default': 3600}
    
    df_processed, pipeline = preprocess_data(df, config)
    
    assert len(df_processed) == len(df)
    assert pipeline is not None
