"""
Unit tests for match_cohorts.py logic (mocked data).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent))

from match_cohorts import prepare_features, nearest_neighbor_matching

def test_prepare_features():
    """Test feature preparation and standardization."""
    # Create mock data
    data = pd.DataFrame({
        'subject_id': [1, 2, 3, 4],
        'age': [25, 30, 35, 40],
        'sex': ['M', 'F', 'M', 'F'],
        'bmi': [22.0, 24.0, 26.0, 28.0],
        'taxa_A': [0.1, 0.2, 0.3, 0.4],
        'taxa_B': [0.5, 0.6, 0.7, 0.8]
    })
    
    X, _, idx, _ = prepare_features(data, data)
    
    assert X.shape[0] == 4
    assert X.shape[1] == 3  # age, bmi, sex_encoded
    assert idx.shape[0] == 4
    
    # Check standardization (mean ~ 0, std ~ 1)
    assert np.allclose(X.mean(axis=0), 0, atol=1e-6)
    assert np.allclose(X.std(axis=0), 1, atol=1e-6)

def test_nearest_neighbor_matching_success():
    """Test NN matching returns pairs when data is close."""
    # Create identical data for source and target
    X = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    idx = np.array(['sub1', 'sub2'])
    
    # Target is same as source
    pairs = nearest_neighbor_matching(X, X, idx, idx, n_neighbors=1)
    
    assert pairs is not None
    assert len(pairs) == 2
    assert 'microbiome_subject_id' in pairs.columns
    assert 'eeg_subject_id' in pairs.columns

def test_nearest_neighbor_matching_insufficient():
    """Test NN matching returns None when pairs < 10."""
    # Create small dataset
    X = np.array([[0.0, 0.0, 0.0]])
    idx = np.array(['sub1'])
    
    pairs = nearest_neighbor_matching(X, X, idx, idx, n_neighbors=1)
    
    assert pairs is None  # Because < 10 pairs