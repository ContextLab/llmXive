"""
Unit tests for the preprocessing pipeline (T013).
"""

import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest

# Add code directory to path if running standalone
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from preprocess import (
    load_ili_data,
    remove_missing_weeks,
    log_transform,
    standardize,
    preprocess_pipeline,
    save_processed_data
)
from exceptions import E_NO_DATA

@pytest.fixture
def sample_raw_data(tmp_path):
    """Create a temporary raw CSV file for testing."""
    data = {
        'REGION': ['US', 'US', 'US', 'US', 'US'],
        'YEAR': [2020, 2020, 2020, 2020, 2020],
        'WEEK': [1, 2, 3, 4, 5],
        '% WEIGHTED ILI': [2.5, 3.0, np.nan, 2.8, 3.2],  # One NaN
        'AGE 0-4': [1.0, 1.1, 1.2, 1.3, 1.4]
    }
    df = pd.DataFrame(data)
    path = os.path.join(tmp_path, 'test_raw.csv')
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def empty_raw_data(tmp_path):
    """Create an empty CSV file for testing."""
    path = os.path.join(tmp_path, 'test_empty.csv')
    pd.DataFrame(columns=['REGION', 'YEAR', 'WEEK', '% WEIGHTED ILI']).to_csv(path, index=False)
    return path

@pytest.fixture
def non_existent_path():
    return '/tmp/non_existent_file_12345.csv'

def test_load_ili_data_success(sample_raw_data):
    df = load_ili_data(sample_raw_data)
    assert len(df) == 5
    assert '% WEIGHTED ILI' in df.columns

def test_load_ili_data_missing_file(non_existent_path):
    with pytest.raises(E_NO_DATA):
        load_ili_data(non_existent_path)

def test_load_ili_data_empty_file(empty_raw_data):
    with pytest.raises(E_NO_DATA):
        load_ili_data(empty_raw_data)

def test_remove_missing_weeks(sample_raw_data):
    df = load_ili_data(sample_raw_data)
    clean_df, count = remove_missing_weeks(df, '% WEIGHTED ILI')
    assert count == 1
    assert len(clean_df) == 4
    assert clean_df['% WEIGHTED ILI'].isna().sum() == 0

def test_log_transform(sample_raw_data):
    df = load_ili_data(sample_raw_data)
    # Remove NaNs first to avoid log(0) or log(nan) issues in this specific test flow
    df, _ = remove_missing_weeks(df, '% WEIGHTED ILI')
    
    df = log_transform(df, '% WEIGHTED ILI', 'ili_log')
    assert 'ili_log' in df.columns
    # Check that log values are finite and not NaN
    assert np.all(np.isfinite(df['ili_log']))
    # Verify log transformation mathematically for the first row (2.5)
    expected = np.log(2.5)
    assert np.isclose(df.iloc[0]['ili_log'], expected)

def test_standardize(sample_raw_data):
    df = load_ili_data(sample_raw_data)
    df, _ = remove_missing_weeks(df, '% WEIGHTED ILI')
    df = log_transform(df, '% WEIGHTED ILI', 'ili_log')
    
    df = standardize(df, 'ili_log', 'ili_standardized')
    assert 'ili_standardized' in df.columns
    
    # Check mean is approx 0 and std approx 1
    mean_val = df['ili_standardized'].mean()
    std_val = df['ili_standardized'].std()
    assert np.isclose(mean_val, 0.0, atol=1e-5)
    assert np.isclose(std_val, 1.0, atol=1e-5)

def test_preprocess_pipeline_integration(sample_raw_data, tmp_path):
    processed_path = os.path.join(tmp_path, 'processed.csv')
    log_path = os.path.join(tmp_path, 'log.json')
    
    # Mock config loading to avoid dependency issues in unit test
    # In real run, load_config() is called. Here we assume defaults or mock it.
    # Since load_config is imported, we might need to mock it if it fails to find config.yaml in temp dir.
    # For this test, we assume config.yaml exists in project root or load_config handles missing gracefully.
    
    df = preprocess_pipeline(
        raw_path=sample_raw_data,
        processed_path=processed_path,
        log_path=log_path
    )
    
    # Verify file creation
    assert os.path.exists(processed_path)
    assert os.path.exists(log_path)
    
    # Verify log content
    with open(log_path, 'r') as f:
        stats = json.load(f)
    
    assert 'missing_weeks_removed' in stats
    assert stats['missing_weeks_removed'] == 1
    assert 'final_records' in stats
    assert stats['final_records'] == 4
    
    # Verify processed data content
    result_df = pd.read_csv(processed_path)
    assert 'ili_standardized' in result_df.columns
    assert len(result_df) == 4

def test_outlier_detection_handling():
    """Test that extreme outliers do not produce inf/nan after log and standardize."""
    data = {
        'REGION': ['US'] * 10,
        'YEAR': [2020] * 10,
        'WEEK': list(range(1, 11)),
        '% WEIGHTED ILI': [2.0] * 9 + [1000.0]  # Extreme outlier
    }
    df = pd.DataFrame(data)
    
    # Simulate pipeline steps
    df, _ = remove_missing_weeks(df, '% WEIGHTED ILI')
    df = log_transform(df, '% WEIGHTED ILI', 'ili_log')
    df = standardize(df, 'ili_log', 'ili_standardized')
    
    # Check for inf or nan
    assert not df['ili_standardized'].isna().any()
    assert not np.isinf(df['ili_standardized']).any()
    
    # The outlier should be standardized but finite
    outlier_std = df.iloc[-1]['ili_standardized']
    # It should be a large positive number, but finite
    assert outlier_std > 5.0  # 1000 vs ~2 should be many sigmas away

def test_constant_series_handling(tmp_path):
    """Test handling of a constant series (std=0)."""
    data = {
        'REGION': ['US'] * 5,
        'YEAR': [2020] * 5,
        'WEEK': list(range(1, 6)),
        '% WEIGHTED ILI': [2.5, 2.5, 2.5, 2.5, 2.5]
    }
    df = pd.DataFrame(data)
    raw_path = os.path.join(tmp_path, 'const_raw.csv')
    df.to_csv(raw_path, index=False)
    
    processed_path = os.path.join(tmp_path, 'const_processed.csv')
    log_path = os.path.join(tmp_path, 'const_log.json')
    
    # This should not crash, but log a warning and set std to 0
    df_out = preprocess_pipeline(
        raw_path=raw_path,
        processed_path=processed_path,
        log_path=log_path
    )
    
    # Verify output exists
    assert os.path.exists(processed_path)
    assert os.path.exists(log_path)
    
    result_df = pd.read_csv(processed_path)
    # Standardized values should be 0.0 for constant series
    assert np.all(result_df['ili_standardized'] == 0.0)