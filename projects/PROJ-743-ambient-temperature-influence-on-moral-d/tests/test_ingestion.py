"""
Tests for the ingestion module.

This file contains unit tests for the data ingestion pipeline,
specifically testing the filtering of invalid records.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions we're testing
from ingestion import (
    filter_invalid_records,
    log_excluded_records,
    ensure_exclusion_log_exists,
    MIN_RESPONSE_TIME_MS,
    MAX_RESPONSE_TIME_MS
)

@pytest.fixture
def sample_moral_machine_data():
    """Create a sample Moral Machine dataset for testing."""
    data = {
        'id': [1, 2, 3, 4, 5, 6, 7, 8],
        'latitude': [40.7128, 51.5074, None, 48.8566, 0.0, 35.6762, 34.0522, 55.7558],
        'longitude': [-74.0060, -0.1278, -73.9352, None, 0.0, 139.6503, -118.2437, 37.6173],
        'response_time_ms': [5000, 15000, 3000, 200, 5000, 50, 100000, 8000]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_log_path():
    """Create a temporary file path for testing the exclusion log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusion_log.csv"
        yield log_path

def test_filter_invalid_records_missing_location(sample_moral_machine_data):
    """Test that records with missing location data are excluded."""
    valid_records, excluded_records = filter_invalid_records(sample_moral_machine_data)
    
    # Should exclude records 3 (missing lat), 4 (missing lon), 5 (lat=0, lon=0)
    assert len(excluded_records) == 3
    assert len(valid_records) == 5
    
    # Check that excluded records have the correct IDs
    excluded_ids = set(excluded_records['id'].tolist())
    assert excluded_ids == {3, 4, 5}

def test_filter_invalid_records_invalid_response_time(sample_moral_machine_data):
    """Test that records with invalid response times are excluded."""
    valid_records, excluded_records = filter_invalid_records(sample_moral_machine_data)
    
    # Should exclude records with response times < 100ms or > 10000ms
    # Records 2 (>10000), 6 (<100), 7 (>10000)
    assert len(excluded_records) == 3
    assert len(valid_records) == 5
    
    # Check that excluded records have the correct IDs
    excluded_ids = set(excluded_records['id'].tolist())
    assert excluded_ids == {2, 6, 7}

def test_filter_invalid_records_combined(sample_moral_machine_data):
    """Test that records with both issues are excluded only once."""
    valid_records, excluded_records = filter_invalid_records(sample_moral_machine_data)
    
    # Total exclusions: 3 (location) + 3 (response time) = 6 unique records
    # But record 5 has both issues, so it should be counted once
    assert len(excluded_records) == 6
    assert len(valid_records) == 2
    
    # Check that valid records are 1 and 8
    valid_ids = set(valid_records['id'].tolist())
    assert valid_ids == {1, 8}

def test_filter_invalid_records_exclusion_reasons(sample_moral_machine_data):
    """Test that exclusion reasons are correctly assigned."""
    valid_records, excluded_records = filter_invalid_records(sample_moral_machine_data)
    
    # Check that each excluded record has an exclusion reason
    assert 'exclusion_reason' in excluded_records.columns
    assert 'details' in excluded_records.columns
    
    # Check specific reasons
    for idx, row in excluded_records.iterrows():
        assert row['exclusion_reason'] != '', f"Record {row['id']} has no exclusion reason"

def test_ensure_exclusion_log_exists(temp_log_path):
    """Test that the exclusion log file is created with the correct header."""
    ensure_exclusion_log_exists(temp_log_path)
    
    assert temp_log_path.exists()
    
    # Check the header
    df = pd.read_csv(temp_log_path)
    expected_columns = ['record_id', 'exclusion_reason', 'details']
    assert list(df.columns) == expected_columns

def test_log_excluded_records(temp_log_path, sample_moral_machine_data):
    """Test that excluded records are logged correctly."""
    valid_records, excluded_records = filter_invalid_records(sample_moral_machine_data)
    
    # Log the excluded records
    log_excluded_records(excluded_records, temp_log_path)
    
    # Check that the log file has the excluded records
    logged_df = pd.read_csv(temp_log_path)
    assert len(logged_df) == len(excluded_records)
    
    # Check that the logged records have the correct IDs
    logged_ids = set(logged_df['record_id'].tolist())
    excluded_ids = set(excluded_records['id'].tolist())
    assert logged_ids == excluded_ids

def test_log_excluded_records_appends(temp_log_path, sample_moral_machine_data):
    """Test that logging excluded records appends to existing log."""
    valid_records, excluded_records = filter_invalid_records(sample_moral_machine_data)
    
    # Log the excluded records twice
    log_excluded_records(excluded_records, temp_log_path)
    log_excluded_records(excluded_records, temp_log_path)
    
    # Check that the log file has the records twice
    logged_df = pd.read_csv(temp_log_path)
    assert len(logged_df) == len(excluded_records) * 2

def test_filter_invalid_records_empty_dataframe():
    """Test that filtering an empty DataFrame works correctly."""
    empty_df = pd.DataFrame(columns=['id', 'latitude', 'longitude', 'response_time_ms'])
    valid_records, excluded_records = filter_invalid_records(empty_df)
    
    assert len(valid_records) == 0
    assert len(excluded_records) == 0

def test_filter_invalid_records_all_valid():
    """Test that all valid records are kept."""
    valid_df = pd.DataFrame({
        'id': [1, 2, 3],
        'latitude': [40.7128, 51.5074, 48.8566],
        'longitude': [-74.0060, -0.1278, 2.3522],
        'response_time_ms': [5000, 8000, 3000]
    })
    
    valid_records, excluded_records = filter_invalid_records(valid_df)
    
    assert len(valid_records) == 3
    assert len(excluded_records) == 0
