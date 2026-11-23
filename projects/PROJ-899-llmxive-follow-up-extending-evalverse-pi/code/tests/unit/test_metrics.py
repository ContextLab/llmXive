import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.models.metrics import (
    load_feature_vectors, 
    load_human_scores, 
    calculate_correlation_for_dimension,
    calculate_dimension_metrics
)

@pytest.fixture
def temp_feature_files():
    """Create temporary feature files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        optical_path = os.path.join(tmpdir, 'features_optical.json')
        audio_path = os.path.join(tmpdir, 'features_audio.json')
        
        # Create mock optical features
        optical_data = [
            {
                "clip_id": "clip_001",
                "dimension": "motion_smoothness",
                "feature_vector": [0.5, 0.6, 0.7],
                "missing_data_flag": False
            },
            {
                "clip_id": "clip_002",
                "dimension": "motion_smoothness",
                "feature_vector": [0.8, 0.9, 1.0],
                "missing_data_flag": False
            },
            {
                "clip_id": "clip_003",
                "dimension": "motion_smoothness",
                "feature_vector": [0.1, 0.2, 0.3],
                "missing_data_flag": True  # Should be excluded
            },
            {
                "clip_id": "clip_004",
                "dimension": "temporal_coherence",
                "feature_vector": [0.4, 0.5, 0.6],
                "missing_data_flag": False
            }
        ]
        
        with open(optical_path, 'w') as f:
            json.dump(optical_data, f)
        
        # Create mock audio features
        audio_data = [
            {
                "clip_id": "clip_005",
                "dimension": "audio_quality",
                "feature_vector": [0.3, 0.4, 0.5],
                "missing_data_flag": False
            }
        ]
        
        with open(audio_path, 'w') as f:
            json.dump(audio_data, f)
        
        yield optical_path, audio_path

@pytest.fixture
def temp_scores_file():
    """Create temporary scores file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scores_path = os.path.join(tmpdir, 'scores.csv')
        
        scores_data = [
            {"clip_id": "clip_001", "dimension": "motion_smoothness", "human_score": 0.7},
            {"clip_id": "clip_002", "dimension": "motion_smoothness", "human_score": 0.9},
            {"clip_id": "clip_003", "dimension": "motion_smoothness", "human_score": 0.2},
            {"clip_id": "clip_004", "dimension": "temporal_coherence", "human_score": 0.6},
            {"clip_id": "clip_005", "dimension": "audio_quality", "human_score": 0.5}
        ]
        
        df = pd.DataFrame(scores_data)
        df.to_csv(scores_path, index=False)
        
        yield scores_path

def test_load_feature_vectors(temp_feature_files):
    """Test loading and filtering of feature vectors."""
    optical_path, audio_path = temp_feature_files
    optical_df, audio_df = load_feature_vectors(optical_path, audio_path)
    
    # Check that missing_data_flag=True samples are excluded
    assert len(optical_df) == 3  # clip_001, clip_002, clip_004 (clip_003 excluded)
    assert len(audio_df) == 1    # clip_005
    
    # Check that clip_003 is not in the dataframe
    assert "clip_003" not in optical_df['clip_id'].values

def test_load_human_scores(temp_scores_file):
    """Test loading of human scores."""
    scores_df = load_human_scores(temp_scores_file)
    
    assert len(scores_df) == 5
    assert 'clip_id' in scores_df.columns
    assert 'dimension' in scores_df.columns
    assert 'human_score' in scores_df.columns

def test_calculate_correlation_for_dimension(temp_feature_files, temp_scores_file):
    """Test correlation calculation for a single dimension."""
    optical_path, audio_path = temp_feature_files
    scores_df = load_human_scores(temp_scores_file)
    optical_df, _ = load_feature_vectors(optical_path, audio_path)
    
    # Test for motion_smoothness dimension
    pearson_r, spearman_r, n_samples = calculate_correlation_for_dimension(
        optical_df, scores_df, 'motion_smoothness'
    )
    
    assert n_samples == 2  # clip_001 and clip_002 (clip_003 excluded due to missing_data_flag)
    assert isinstance(pearson_r, float)
    assert isinstance(spearman_r, float)
    assert -1.0 <= pearson_r <= 1.0
    assert -1.0 <= spearman_r <= 1.0

def test_calculate_dimension_metrics(temp_feature_files, temp_scores_file):
    """Test full dimension metrics calculation and CSV output."""
    optical_path, audio_path = temp_feature_files
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'correlations_point.csv')
        
        result_df = calculate_dimension_metrics(
            optical_path, 
            audio_path, 
            temp_scores_file,
            output_path
        )
        
        # Check that output file was created
        assert os.path.exists(output_path)
        
        # Check DataFrame structure
        assert 'dimension' in result_df.columns
        assert 'pearson_r' in result_df.columns
        assert 'spearman_r' in result_df.columns
        
        # Check that we have results for all dimensions
        dimensions = result_df['dimension'].unique()
        assert 'motion_smoothness' in dimensions
        assert 'temporal_coherence' in dimensions
        assert 'audio_quality' in dimensions
        
        # Check CSV content
        csv_df = pd.read_csv(output_path)
        assert len(csv_df) == len(result_df)
        assert list(csv_df.columns) == ['dimension', 'pearson_r', 'spearman_r']