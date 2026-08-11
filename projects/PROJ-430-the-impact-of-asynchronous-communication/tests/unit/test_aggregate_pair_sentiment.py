"""
Unit tests for aggregate_pair_sentiment.py (T021b).

Tests:
1. Verify output file is created
2. Verify schema (pair_id, mean_sentiment, count)
3. Verify non-null values
4. Verify aggregation logic (mean calculation)
"""
import os
import tempfile
from pathlib import Path
import json
import pytest
import pandas as pd
import numpy as np

# Import the module under test
from code.aggregate_pair_sentiment import (
    load_timestamp_features,
    load_raw_events,
    extract_pair_sentiment,
    merge_and_fill,
    run_aggregate_pair_sentiment
)
from code.config import get_config

@pytest.fixture
def sample_timestamp_features():
    """Sample timestamp features data."""
    return pd.DataFrame({
        'project_id': ['proj1', 'proj1', 'proj2'],
        'pair_id': ['pair1', 'pair2', 'pair1'],
        'response_time_variance': [100.5, 200.3, 150.7],
        'mean_delay': [10.5, 20.3, 15.7],
        'pair_count': [5, 3, 4]
    })

@pytest.fixture
def sample_events():
    """Sample events data with sentiment."""
    return pd.DataFrame({
        'project_id': ['proj1', 'proj1', 'proj1', 'proj2', 'proj2'],
        'pair_id': ['pair1', 'pair1', 'pair2', 'pair1', 'pair1'],
        'comment_id': ['c1', 'c2', 'c3', 'c4', 'c5'],
        'sentiment_compound': [0.8, 0.6, -0.5, 0.3, 0.7]
    })

def test_extract_pair_sentiment_aggregation(sample_timestamp_features, sample_events):
    """Test that sentiment is correctly aggregated by pair."""
    result = extract_pair_sentiment(sample_timestamp_features, sample_events)
    
    # Check columns
    assert 'project_id' in result.columns
    assert 'pair_id' in result.columns
    assert 'mean_sentiment' in result.columns
    assert 'count' in result.columns
    
    # Check row count (should be 3 unique pairs)
    assert len(result) == 3
    
    # Verify mean calculation for proj1, pair1
    # Comments: c1 (0.8), c2 (0.6) -> mean = 0.7, count = 2
    pair1_row = result[(result['project_id'] == 'proj1') & (result['pair_id'] == 'pair1')]
    assert len(pair1_row) == 1
    assert np.isclose(pair1_row['mean_sentiment'].values[0], 0.7, atol=0.01)
    assert pair1_row['count'].values[0] == 2
    
    # Verify mean calculation for proj1, pair2
    # Comments: c3 (-0.5) -> mean = -0.5, count = 1
    pair2_row = result[(result['project_id'] == 'proj1') & (result['pair_id'] == 'pair2')]
    assert len(pair2_row) == 1
    assert np.isclose(pair2_row['mean_sentiment'].values[0], -0.5, atol=0.01)
    assert pair2_row['count'].values[0] == 1

def test_merge_and_fill(sample_timestamp_features, sample_events):
    """Test merging and filling missing values."""
    sentiment_df = extract_pair_sentiment(sample_timestamp_features, sample_events)
    
    # Create a timestamp df with an extra pair that has no sentiment
    extra_timestamp = sample_timestamp_features.copy()
    extra_timestamp = extra_timestamp.append({
        'project_id': 'proj2',
        'pair_id': 'pair2',
        'response_time_variance': 50.0,
        'mean_delay': 5.0,
        'pair_count': 2
    }, ignore_index=True)
    
    merged = merge_and_fill(extra_timestamp, sentiment_df)
    
    # Check that the extra pair has filled values
    extra_pair = merged[(merged['project_id'] == 'proj2') & (merged['pair_id'] == 'pair2')]
    assert len(extra_pair) == 1
    assert extra_pair['mean_sentiment'].values[0] == 0  # Filled with 0
    assert extra_pair['count'].values[0] == 0

def test_run_aggregate_pair_sentiment_creates_file(sample_timestamp_features, sample_events, tmp_path):
    """Test that the pipeline creates the output parquet file."""
    # Mock the load functions to return our sample data
    import code.aggregate_pair_sentiment as agg_module
    
    original_load_ts = agg_module.load_timestamp_features
    original_load_events = agg_module.load_raw_events
    
    def mock_load_ts(config):
        return sample_timestamp_features
    
    def mock_load_events(config):
        return sample_events
    
    agg_module.load_timestamp_features = mock_load_ts
    agg_module.load_raw_events = mock_load_events
    
    try:
        output_path = tmp_path / "test_pair_sentiment.parquet"
        config = get_config()
        config['pair_sentiment_path'] = str(output_path)
        config['timestamp_features_path'] = '/dev/null'  # Not used due to mock
        config['raw_events_path'] = '/dev/null'  # Not used due to mock
        
        result = run_aggregate_pair_sentiment(config)
        
        # Check file exists
        assert output_path.exists()
        
        # Check content
        loaded = pd.read_parquet(output_path)
        assert len(loaded) == 3
        assert 'pair_id' in loaded.columns
        assert 'mean_sentiment' in loaded.columns
        assert 'count' in loaded.columns
    finally:
        # Restore original functions
        agg_module.load_timestamp_features = original_load_ts
        agg_module.load_raw_events = original_load_events

def test_output_schema_compliance(sample_timestamp_features, sample_events):
    """Test that output matches the required schema for T021b."""
    result = extract_pair_sentiment(sample_timestamp_features, sample_events)
    
    # Required columns: pair_id, mean_sentiment, count (and project_id for context)
    required_columns = ['project_id', 'pair_id', 'mean_sentiment', 'count']
    for col in required_columns:
        assert col in result.columns, f"Missing required column: {col}"
    
    # Check data types
    assert result['mean_sentiment'].dtype in [np.float64, np.float32]
    assert result['count'].dtype in [np.int64, np.int32]
    
    # Check for non-null values
    assert result['mean_sentiment'].notna().all()
    assert result['count'].notna().all()
    assert (result['count'] >= 0).all()