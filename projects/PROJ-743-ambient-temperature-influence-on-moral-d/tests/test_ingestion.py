"""
Tests for T017: Load, Filter & Count.

These tests verify the ingestion pipeline's filtering logic and logging behavior.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import (
    load_moral_machine_data,
    apply_column_mapping,
    filter_missing_location,
    filter_invalid_response_time,
    capture_pre_filter_count,
    log_counts_to_file,
    ensure_exclusion_log_exists
)

@pytest.fixture
def sample_moral_machine_data():
    """Create sample Moral Machine data for testing."""
    data = {
        'participant_id': range(10),
        'lat': [40.7128, 51.5074, 35.6762, 48.8566, 52.5200, 34.0522, 41.8781, 37.7749, 47.6062, 38.9072],
        'lon': [-74.0060, -0.1278, 139.6503, 2.3522, 13.4050, -118.2437, -87.6298, -122.4194, -122.3321, -77.0369],
        'response_time_ms': [500, 1200, 800, 200, 15000, 300, 900, 600, 1100, 700],
        'country': ['US', 'UK', 'JP', 'FR', 'DE', 'US', 'US', 'US', 'US', 'US'],
        'dilemma_id': range(10)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_apply_column_mapping(sample_moral_machine_data):
    """Test that column mapping works correctly."""
    df = apply_column_mapping(sample_moral_machine_data.copy())
    
    assert 'latitude' in df.columns
    assert 'longitude' in df.columns
    assert 'response_time' in df.columns
    assert 'lat' not in df.columns
    assert 'lon' not in df.columns
    assert 'response_time_ms' not in df.columns

def test_filter_missing_location_valid(temp_dir):
    """Test filtering when all locations are valid."""
    data = {
        'latitude': [40.7128, 51.5074, 35.6762],
        'longitude': [-74.0060, -0.1278, 139.6503]
    }
    df = pd.DataFrame(data)
    exclusion_log = temp_dir / 'exclusion_log.csv'
    
    filtered_df, excluded_count = filter_missing_location(df, exclusion_log)
    
    assert excluded_count == 0
    assert len(filtered_df) == 3

def test_filter_missing_location_invalid(temp_dir):
    """Test filtering when some locations are missing."""
    data = {
        'latitude': [40.7128, np.nan, 35.6762, 48.8566],
        'longitude': [-74.0060, -0.1278, np.nan, 2.3522]
    }
    df = pd.DataFrame(data)
    exclusion_log = temp_dir / 'exclusion_log.csv'
    
    filtered_df, excluded_count = filter_missing_location(df, exclusion_log)
    
    assert excluded_count == 2
    assert len(filtered_df) == 2
    
    # Check exclusion log was created
    assert exclusion_log.exists()

def test_filter_invalid_response_time_valid(temp_dir):
    """Test filtering when all response times are valid."""
    data = {
        'response_time': [500, 1200, 800, 200, 1500]
    }
    df = pd.DataFrame(data)
    exclusion_log = temp_dir / 'exclusion_log.csv'
    
    filtered_df, excluded_count = filter_invalid_response_time(
        df, exclusion_log, min_ms=100, max_ms=10000
    )
    
    assert excluded_count == 0
    assert len(filtered_df) == 5

def test_filter_invalid_response_time_invalid(temp_dir):
    """Test filtering when some response times are invalid."""
    data = {
        'response_time': [50, 1200, 80, 200, 15000, 300]
    }
    df = pd.DataFrame(data)
    exclusion_log = temp_dir / 'exclusion_log.csv'
    
    filtered_df, excluded_count = filter_invalid_response_time(
        df, exclusion_log, min_ms=100, max_ms=10000
    )
    
    assert excluded_count == 3  # 50, 80, 15000 are invalid
    assert len(filtered_df) == 3

def test_capture_pre_filter_count(temp_dir):
    """Test that pre-filter count is captured correctly."""
    data = {
        'latitude': [40.7128, 51.5074, np.nan, 48.8566],
        'longitude': [-74.0060, -0.1278, -0.1278, np.nan]
    }
    df = pd.DataFrame(data)
    counts_log = temp_dir / 'counts.json'
    
    capture_pre_filter_count(df, counts_log)
    
    assert counts_log.exists()
    with open(counts_log, 'r') as f:
        counts = json.load(f)
    
    assert 'count_total_original_valid_location' in counts
    assert counts['count_total_original_valid_location'] == 2  # Only 2 have both lat and lon

def test_log_counts_to_file(temp_dir):
    """Test that counts are logged correctly."""
    counts_log = temp_dir / 'counts.json'
    
    log_counts_to_file(
        counts_log,
        count_filtered=100,
        count_missing_location=10,
        count_invalid_response_time=5
    )
    
    assert counts_log.exists()
    with open(counts_log, 'r') as f:
        counts = json.load(f)
    
    assert counts['count_filtered_for_analysis'] == 100
    assert counts['count_excluded_missing_location'] == 10
    assert counts['count_excluded_invalid_response_time'] == 5

def test_ensure_exclusion_log_exists(temp_dir):
    """Test that exclusion log file is created if it doesn't exist."""
    exclusion_log = temp_dir / 'exclusion_log.csv'
    
    ensure_exclusion_log_exists(exclusion_log)
    
    assert exclusion_log.exists()
    with open(exclusion_log, 'r') as f:
        content = f.read()
    
    assert 'record_id,exclusion_reason,original_data' in content