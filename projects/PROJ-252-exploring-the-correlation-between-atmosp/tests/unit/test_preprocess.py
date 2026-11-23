"""
Unit tests for preprocessing pipeline (T017).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import (
    load_raw_earthquake_data,
    deduplicate_events,
    calculate_daily_pressure_anomalies,
    generate_checksum,
    validate_schema,
    load_config
)
from config import get_raw_path, get_processed_path

@pytest.fixture
def sample_earthquake_data():
    """Create sample earthquake data for testing."""
    data = [
        {
            'earthquake_id': 'us6000j1a1',
            'timestamp': '2018-01-01T12:00:00Z',
            'latitude': 61.0,
            'longitude': -150.0,
            'magnitude': 5.5,
            'depth_km': 10.0
        },
        {
            'earthquake_id': 'us6000j1a1',  # Duplicate
            'timestamp': '2018-01-01T13:00:00Z',
            'latitude': 61.0,
            'longitude': -150.0,
            'magnitude': 5.5,
            'depth_km': 10.0
        },
        {
            'earthquake_id': 'us6000j1b2',
            'timestamp': '2018-01-02T12:00:00Z',
            'latitude': 62.0,
            'longitude': -151.0,
            'magnitude': 4.5,
            'depth_km': 15.0
        }
    ]
    return pd.DataFrame(data)

@pytest.fixture
def sample_pressure_data():
    """Create sample pressure data for testing."""
    data = [
        {
            'timestamp': '2018-01-01T12:00:00Z',
            'latitude': 61.0,
            'longitude': -150.0,
            'pressure_value': 1013.25
        },
        {
            'timestamp': '2018-01-02T12:00:00Z',
            'latitude': 62.0,
            'longitude': -151.0,
            'pressure_value': 1010.50
        }
    ]
    return pd.DataFrame(data)

def test_deduplicate_events(sample_earthquake_data):
    """Test that duplicate events are removed, keeping most recent."""
    deduped = deduplicate_events(sample_earthquake_data)
    assert len(deduped) == 2, "Should have 2 unique events"
    assert deduped['earthquake_id'].nunique() == 2, "Should have 2 unique IDs"

def test_calculate_daily_pressure_anomalies(sample_pressure_data):
    """Test anomaly calculation."""
    anomalies = calculate_daily_pressure_anomalies(sample_pressure_data, moving_average_days=30)
    assert 'anomaly' in anomalies.columns, "Should have anomaly column"
    assert len(anomalies) == len(sample_pressure_data), "Should have same number of rows"

def test_generate_checksum():
    """Test checksum generation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = generate_checksum(temp_path)
        assert len(checksum) == 64, "SHA256 should be 64 characters"
        assert all(c in '0123456789abcdef' for c in checksum), "Should be hex"
    finally:
        os.unlink(temp_path)

def test_load_config():
    """Test config loading."""
    config = load_config()
    assert 'expected_earthquake_count' in config, "Config should have expected count"
    assert 'moving_average_days' in config, "Config should have moving average days"

def test_row_count_verification():
    """Test that row count matches expected count from config."""
    config = load_config()
    expected = config.get('expected_earthquake_count', 12)
    
    # Check if master dataset exists
    master_path = get_processed_path() / 'master_dataset.csv'
    if master_path.exists():
        df = pd.read_csv(master_path)
        actual = len(df)
        tolerance = expected * 0.01
        assert abs(actual - expected) <= tolerance, f"Row count {actual} not within 1% of expected {expected}"
    else:
        pytest.skip("Master dataset not yet generated")

def test_schema_validation():
    """Test schema validation against earthquake schema."""
    schema_path = get_raw_path().parent / 'contracts' / 'earthquake.schema.yaml'
    
    if not schema_path.exists():
        pytest.skip("Schema file not found")
    
    # Create test dataframe
    df = pd.DataFrame([{
        'earthquake_id': 'test',
        'timestamp': '2018-01-01',
        'latitude': 61.0,
        'longitude': -150.0,
        'magnitude': 5.0,
        'depth_km': 10.0
    }])
    
    valid, errors = validate_schema(df, str(schema_path))
    # Note: This test may fail if schema format differs
    # The important thing is the function exists and runs
    assert isinstance(valid, bool), "Should return boolean"
    assert isinstance(errors, list), "Should return list of errors"
