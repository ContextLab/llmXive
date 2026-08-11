"""
Integration tests for the ingestion pipeline implementation (T010).

These tests verify that the ingestion module correctly:
1. Loads pH and temperature CSV files
2. Validates required metadata fields
3. Calculates pH heterogeneity within ±15 minute windows
4. Handles temporal alignment
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta
import logging

from ingestion import (
    load_sensor_data,
    validate_metadata_fields,
    align_temporal_data,
    calculate_pH_heterogeneity_for_window,
    run_ingestion_pipeline
)
from utils import get_logger

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_ph_data():
    """Generate sample pH data for testing."""
    base_time = datetime(2023, 6, 15, 10, 0, 0)
    data = []
    
    for i in range(10):
        ts = base_time + timedelta(minutes=i*5)
        data.append({
            'timestamp': ts,
            'pH': 7.5 + (i % 3) * 0.1,
            'deployment_event': 'DEPLOY-001',
            'sensor_id': 'SENSOR-A',
            'coordinates': '32.5N,125.3W'
        })
    
    # Add some data with edge cases
    data.append({
        'timestamp': base_time + timedelta(minutes=52),
        'pH': 0.5,  # Outlier
        'deployment_event': 'DEPLOY-001',
        'sensor_id': 'SENSOR-A',
        'coordinates': '32.5N,125.3W'
    })
    
    data.append({
        'timestamp': base_time + timedelta(minutes=57),
        'pH': 10.5,  # Outlier
        'deployment_event': 'DEPLOY-001',
        'sensor_id': 'SENSOR-A',
        'coordinates': '32.5N,125.3W'
    })
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_temp_data():
    """Generate sample temperature data for testing."""
    base_time = datetime(2023, 6, 15, 10, 0, 0)
    data = []
    
    for i in range(10):
        ts = base_time + timedelta(minutes=i*5)
        data.append({
            'timestamp': ts,
            'temperature': 2.5 + (i % 3) * 0.1
        })
    
    return pd.DataFrame(data)

def test_load_sensor_data_valid_file(temp_test_dir, sample_ph_data):
    """Test loading a valid sensor data file."""
    file_path = temp_test_dir / "test_ph.csv"
    sample_ph_data.to_csv(file_path, index=False)
    
    logger = get_logger('test')
    loaded_df = load_sensor_data(file_path, 'pH', logger)
    
    assert len(loaded_df) == len(sample_ph_data)
    assert 'timestamp' in loaded_df.columns
    assert 'pH' in loaded_df.columns
    assert pd.api.types.is_datetime64_any_dtype(loaded_df['timestamp'])

def test_load_sensor_data_missing_file(temp_test_dir):
    """Test loading a missing sensor data file raises error."""
    file_path = temp_test_dir / "nonexistent.csv"
    logger = get_logger('test')
    
    with pytest.raises(FileNotFoundError):
        load_sensor_data(file_path, 'pH', logger)

def test_validate_metadata_fields_valid(sample_ph_data):
    """Test validation passes with valid metadata."""
    logger = get_logger('test')
    is_valid, missing_fields = validate_metadata_fields(sample_ph_data, logger)
    
    assert is_valid is True
    assert len(missing_fields) == 0

def test_validate_metadata_fields_missing_column(sample_ph_data):
    """Test validation fails when required column is missing."""
    df = sample_ph_data.drop(columns=['deployment_event'])
    logger = get_logger('test')
    
    is_valid, missing_fields = validate_metadata_fields(df, logger)
    
    assert is_valid is False
    assert any('deployment_event' in field for field in missing_fields)

def test_validate_metadata_fields_empty_values(sample_ph_data):
    """Test validation fails when required field has empty values."""
    df = sample_ph_data.copy()
    df.loc[0, 'sensor_id'] = ''
    logger = get_logger('test')
    
    is_valid, missing_fields = validate_metadata_fields(df, logger)
    
    assert is_valid is False
    assert any('sensor_id' in field for field in missing_fields)

def test_align_temporal_data(temp_test_dir, sample_ph_data, sample_temp_data):
    """Test temporal alignment of pH and temperature data."""
    logger = get_logger('test')
    
    unified_df, rejected_samples = align_temporal_data(
        sample_ph_data, 
        sample_temp_data, 
        logger
    )
    
    # Should have aligned most samples
    assert len(unified_df) > 0
    assert 'pH' in unified_df.columns
    assert 'temperature' in unified_df.columns
    assert 'timestamp' in unified_df.columns

def test_calculate_ph_heterogeneity(sample_ph_data):
    """Test pH heterogeneity calculation."""
    logger = get_logger('test')
    
    result_df = calculate_pH_heterogeneity_for_window(sample_ph_data, logger)
    
    assert 'pH_sd' in result_df.columns
    assert 'pH_heterogeneous' in result_df.columns
    assert all(result_df['pH_sd'] >= 0)
    assert all(result_df['pH_heterogeneous'].isin([True, False]))

def test_run_ingestion_pipeline_full(temp_test_dir, sample_ph_data, sample_temp_data):
    """Test the complete ingestion pipeline."""
    # Save test data
    ph_file = temp_test_dir / "pH_log.csv"
    temp_file = temp_test_dir / "temperature_log.csv"
    output_file = temp_test_dir / "unified_sample_table.csv"
    rejected_log_file = temp_test_dir / "rejected_samples.log"
    
    sample_ph_data.to_csv(ph_file, index=False)
    sample_temp_data.to_csv(temp_file, index=False)
    
    logger = get_logger('test')
    
    results = run_ingestion_pipeline(
        ph_file=ph_file,
        temp_file=temp_file,
        output_file=output_file,
        rejected_log_file=rejected_log_file,
        logger=logger
    )
    
    # Verify results
    assert results['ph_rows_loaded'] > 0
    assert results['temp_rows_loaded'] > 0
    assert results['aligned_samples'] > 0
    assert results['metadata_valid'] is True
    
    # Verify output file exists
    assert output_file.exists()
    
    # Verify output content
    output_df = pd.read_csv(output_file)
    assert len(output_df) == results['aligned_samples']
    assert 'pH_sd' in output_df.columns
    assert 'pH_heterogeneous' in output_df.columns
    assert 'deployment_event' in output_df.columns
    assert 'sensor_id' in output_df.columns
    assert 'coordinates' in output_df.columns
    
    # Verify rejected log file exists
    assert rejected_log_file.exists()