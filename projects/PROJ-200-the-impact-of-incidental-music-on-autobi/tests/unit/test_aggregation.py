"""
Unit tests for the aggregation module.

Tests the `aggregate_to_user_track` function to ensure it correctly
aggregates data to the User-Track Pair level.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function to test
from aggregation import aggregate_to_user_track, join_exposure_data

@pytest.fixture
def sample_joined_data():
    """Create a sample joined DataFrame for testing."""
    data = {
        'user_id': ['U1', 'U1', 'U1', 'U2', 'U2', 'U3'],
        'track_id': ['T1', 'T1', 'T2', 'T1', 'T2', 'T1'],
        'vividness': [5.0, 4.0, 3.0, 5.0, 4.0, 2.0],
        'valence': [1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
        'adolescent_exposure_score': [0.8, 0.8, 0.2, 0.8, 0.2, 0.8],
        'residualized_exposure_score': [0.1, 0.1, -0.1, 0.1, -0.1, 0.1],
        'overall_popularity_score': [100, 100, 50, 100, 50, 100]
    }
    return pd.DataFrame(data)

def test_aggregate_to_user_track_basic(sample_joined_data):
    """Test basic aggregation functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.parquet')
        output_path = os.path.join(tmpdir, 'output.parquet')
        
        sample_joined_data.to_parquet(input_path)
        
        result = aggregate_to_user_track(input_path, output_path)
        
        # Check output file exists
        assert os.path.exists(output_path)
        
        # Check shape: U1-T1 (2 rows -> 1), U1-T2 (1 row -> 1), U2-T1 (1 row -> 1), U2-T2 (1 row -> 1), U3-T1 (1 row -> 1)
        # Total 5 pairs
        assert len(result) == 5
        
        # Check columns
        expected_cols = ['user_id', 'track_id', 'mean_vividness', 'mean_valence',
                         'adolescent_exposure_score', 'residualized_exposure_score',
                         'overall_popularity_score', 'cue_count']
        assert list(result.columns) == expected_cols
        
        # Check specific aggregation: U1-T1 should have mean vividness (5+4)/2 = 4.5
        u1_t1 = result[(result['user_id'] == 'U1') & (result['track_id'] == 'T1')]
        assert len(u1_t1) == 1
        assert u1_t1['mean_vividness'].values[0] == 4.5
        assert u1_t1['mean_valence'].values[0] == 1.5
        assert u1_t1['cue_count'].values[0] == 2

def test_aggregate_to_user_track_min_cues(sample_joined_data):
    """Test filtering by minimum cues per pair."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.parquet')
        output_path = os.path.join(tmpdir, 'output.parquet')
        
        sample_joined_data.to_parquet(input_path)
        
        # Filter for pairs with at least 2 cues
        result = aggregate_to_user_track(input_path, output_path, min_cues_per_pair=2)
        
        # Only U1-T1 has 2 cues
        assert len(result) == 1
        assert result['cue_count'].values[0] == 2

def test_aggregate_to_user_track_missing_columns(sample_joined_data):
    """Test that missing columns raise an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.parquet')
        output_path = os.path.join(tmpdir, 'output.parquet')
        
        # Remove a required column
        bad_data = sample_joined_data.drop(columns=['vividness'])
        bad_data.to_parquet(input_path)
        
        with pytest.raises(ValueError) as exc_info:
            aggregate_to_user_track(input_path, output_path)
        
        assert 'vividness' in str(exc_info.value)
