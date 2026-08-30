import os
import sys
import json
import tempfile
import pickle
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.metrics import prepare_correlation_data, load_feature_vectors, load_human_scores

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_optical_features(temp_data_dir):
    """Create sample optical features file."""
    data = [
        {
            "clip_id": "clip_001",
            "dimension": "motion_smoothness",
            "feature_vector": [0.5, 0.6, 0.7],
            "missing_data_flag": False
        },
        {
            "clip_id": "clip_002",
            "dimension": "motion_smoothness",
            "feature_vector": [0.4, 0.5, 0.6],
            "missing_data_flag": False
        },
        {
            "clip_id": "clip_003",
            "dimension": "motion_smoothness",
            "feature_vector": [0.3, 0.4, 0.5],
            "missing_data_flag": True  # Should be filtered out
        },
        {
            "clip_id": "clip_001",
            "dimension": "visual_clarity",
            "feature_vector": [0.8, 0.9],
            "missing_data_flag": False
        }
    ]
    
    file_path = os.path.join(temp_data_dir, 'features_optical.json')
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    return file_path

@pytest.fixture
def sample_audio_features(temp_data_dir):
    """Create sample audio features file."""
    data = [
        {
            "clip_id": "clip_001",
            "dimension": "motion_smoothness",
            "feature_vector": [0.2, 0.3],
            "missing_data_flag": False
        },
        {
            "clip_id": "clip_002",
            "dimension": "motion_smoothness",
            "feature_vector": [0.1, 0.2],
            "missing_data_flag": False
        },
        {
            "clip_id": "clip_001",
            "dimension": "visual_clarity",
            "feature_vector": [0.7, 0.8],
            "missing_data_flag": False
        }
    ]
    
    file_path = os.path.join(temp_data_dir, 'features_audio.json')
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    return file_path

@pytest.fixture
def sample_scores(temp_data_dir):
    """Create sample scores CSV file."""
    data = {
        'clip_id': ['clip_001', 'clip_002', 'clip_003', 'clip_001'],
        'dimension': ['motion_smoothness', 'motion_smoothness', 'motion_smoothness', 'visual_clarity'],
        'human_score': [0.8, 0.7, 0.6, 0.9],
        'vlm_proxy_score': [0.75, 0.65, 0.55, 0.85]
    }
    
    file_path = os.path.join(temp_data_dir, 'scores.csv')
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return file_path

def test_load_feature_vectors(sample_optical_features):
    """Test loading feature vectors from JSON."""
    data = load_feature_vectors(sample_optical_features)
    
    assert isinstance(data, list)
    assert len(data) == 4
    assert data[0]['clip_id'] == 'clip_001'
    assert data[0]['dimension'] == 'motion_smoothness'

def test_load_human_scores(sample_scores):
    """Test loading human scores from CSV."""
    df = load_human_scores(sample_scores)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert 'clip_id' in df.columns
    assert 'human_score' in df.columns

def test_prepare_correlation_data_filters_missing(sample_optical_features, sample_audio_features, sample_scores, temp_data_dir):
    """Test that prepare_correlation_data filters out missing_data_flag=True."""
    output_path = os.path.join(temp_data_dir, 'correlation_data.pkl')
    
    prepare_correlation_data(
        sample_optical_features,
        sample_audio_features,
        sample_scores,
        output_path
    )
    
    assert os.path.exists(output_path)
    
    with open(output_path, 'rb') as f:
        data = pickle.load(f)
    
    # Should have 2 dimensions
    assert 'motion_smoothness' in data
    assert 'visual_clarity' in data
    
    # motion_smoothness should have 2 samples (clip_001 and clip_002, clip_003 filtered out)
    assert len(data['motion_smoothness']['human_scores']) == 2
    
    # visual_clarity should have 1 sample
    assert len(data['visual_clarity']['human_scores']) == 1

def test_prepare_correlation_data_creates_arrays(sample_optical_features, sample_audio_features, sample_scores, temp_data_dir):
    """Test that prepare_correlation_data creates proper numpy arrays."""
    output_path = os.path.join(temp_data_dir, 'correlation_data.pkl')
    
    prepare_correlation_data(
        sample_optical_features,
        sample_audio_features,
        sample_scores,
        output_path
    )
    
    with open(output_path, 'rb') as f:
        data = pickle.load(f)
    
    # Check that features are numpy arrays
    assert isinstance(data['motion_smoothness']['optical_features'], np.ndarray)
    assert isinstance(data['motion_smoothness']['audio_features'], np.ndarray)
    assert isinstance(data['motion_smoothness']['human_scores'], np.ndarray)
    
    # Check dimensions
    assert data['motion_smoothness']['optical_features'].shape[0] == 2
    assert data['motion_smoothness']['audio_features'].shape[0] == 2
    assert data['motion_smoothness']['human_scores'].shape[0] == 2