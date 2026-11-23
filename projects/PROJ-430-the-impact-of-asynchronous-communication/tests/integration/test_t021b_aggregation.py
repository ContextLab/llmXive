"""
Integration test for T021b: Aggregate Pair Sentiment.

This test verifies that:
1. The script runs without error.
2. The output file `data/derived/pair_sentiment.parquet` is created.
3. The schema matches the specification (pair_id, mean_sentiment, count).
4. Values are reasonable (mean_sentiment between -1 and 1, count >= 0).
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_config, ensure_directories_exist
from aggregate_pair_sentiment import run_aggregate_pair_sentiment, load_timestamp_features, load_raw_events

@pytest.fixture
def mock_env():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create directories
    (project_root / "data" / "raw").mkdir(parents=True)
    (project_root / "data" / "derived").mkdir(parents=True)
    (project_root / "data" / "validation").mkdir(parents=True)
    (project_root / "data" / "logs").mkdir(parents=True)
    
    # Create a mock config file
    config_data = {
        "data": {
            "root": str(project_root / "data"),
            "raw": str(project_root / "data" / "raw"),
            "derived": str(project_root / "data" / "derived"),
            "validation": str(project_root / "data" / "validation"),
            "logs": str(project_root / "data" / "logs")
        },
        "api": {
            "github_token": "fake_token"
        },
        "thresholds": {
            "min_events": 5,
            "sample_size": 10
        }
    }
    
    config_path = project_root / "config.json"
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    
    # Set environment variable to point to config
    os.environ["PROJECT_CONFIG"] = str(config_path)
    
    # Create mock input files
    # 1. Mock timestamp_features.parquet
    mock_timestamps = pd.DataFrame({
        'pair_id': ['pair_A', 'pair_B', 'pair_C'],
        'project_id': ['proj_1', 'proj_1', 'proj_2'],
        'response_time_variance': [10.5, 20.0, 15.0],
        'mean_delay': [5.0, 10.0, 8.0]
    })
    mock_timestamps.to_parquet(project_root / "data" / "derived" / "timestamp_features.parquet")
    
    # 2. Mock events.json with sentiment data
    mock_events = [
        {
            "pair_id": "pair_A",
            "project_id": "proj_1",
            "body": "This is a great idea! I love it.",
            "type": "comment"
        },
        {
            "pair_id": "pair_A",
            "project_id": "proj_1",
            "body": "I disagree, this is terrible.",
            "type": "comment"
        },
        {
            "pair_id": "pair_B",
            "project_id": "proj_1",
            "body": "Thanks for the help.",
            "type": "comment"
        },
        {
            "pair_id": "pair_C",
            "project_id": "proj_2",
            "body": "Non-English text here: Hola mundo", # Should be filtered by langdetect
            "type": "comment"
        },
        {
            "pair_id": "pair_D", # Not in timestamp_features, should be skipped
            "project_id": "proj_3",
            "body": "This should be ignored.",
            "type": "comment"
        }
    ]
    
    with open(project_root / "data" / "raw" / "events.json", 'w') as f:
        json.dump(mock_events, f)
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)
    if "PROJECT_CONFIG" in os.environ:
        del os.environ["PROJECT_CONFIG"]

def test_t021b_output_creation(mock_env):
    """Test that the script creates the output file."""
    # Run the aggregation
    run_aggregate_pair_sentiment()
    
    output_path = mock_env / "data" / "derived" / "pair_sentiment.parquet"
    assert output_path.exists(), "Output file pair_sentiment.parquet was not created"

def test_t021b_schema(mock_env):
    """Test that the output schema is correct."""
    run_aggregate_pair_sentiment()
    
    output_path = mock_env / "data" / "derived" / "pair_sentiment.parquet"
    df = pd.read_parquet(output_path)
    
    required_cols = {'pair_id', 'mean_sentiment', 'count'}
    assert required_cols.issubset(set(df.columns)), f"Missing columns: {required_cols - set(df.columns)}"

def test_t021b_values(mock_env):
    """Test that values are within expected ranges."""
    run_aggregate_pair_sentiment()
    
    output_path = mock_env / "data" / "derived" / "pair_sentiment.parquet"
    df = pd.read_parquet(output_path)
    
    # mean_sentiment (VADER compound) should be between -1 and 1
    assert df['mean_sentiment'].min() >= -1.0, "mean_sentiment below -1"
    assert df['mean_sentiment'].max() <= 1.0, "mean_sentiment above 1"
    
    # count should be non-negative
    assert (df['count'] >= 0).all(), "Negative count found"
    
    # Check specific pairs
    # pair_A: 2 comments (one positive, one negative) -> mean should be around 0
    # pair_B: 1 comment (positive) -> mean > 0
    # pair_C: 0 valid English comments (filtered) -> mean = 0.0, count = 0
    
    pair_a = df[df['pair_id'] == 'pair_A']
    assert len(pair_a) == 1
    assert pair_a['count'].iloc[0] == 2
    
    pair_c = df[df['pair_id'] == 'pair_C']
    assert len(pair_c) == 1
    assert pair_c['count'].iloc[0] == 0
    assert pair_c['mean_sentiment'].iloc[0] == 0.0

def test_t021b_missing_pair_handling(mock_env):
    """Test that pairs in events but not in timestamp_features are ignored."""
    run_aggregate_pair_sentiment()
    
    output_path = mock_env / "data" / "derived" / "pair_sentiment.parquet"
    df = pd.read_parquet(output_data)
    
    # pair_D should not be in the output
    assert 'pair_D' not in df['pair_id'].values, "pair_D should be excluded"

def test_t021b_empty_sentiment_fallback(mock_env):
    """Test that pairs with no sentiment data get 0.0 and count 0."""
    run_aggregate_pair_sentiment()
    
    output_path = mock_env / "data" / "derived" / "pair_sentiment.parquet"
    df = pd.read_parquet(output_path)
    
    # pair_C had non-English text, so it should have 0 sentiment and 0 count
    pair_c = df[df['pair_id'] == 'pair_C']
    assert pair_c['mean_sentiment'].iloc[0] == 0.0
    assert pair_c['count'].iloc[0] == 0