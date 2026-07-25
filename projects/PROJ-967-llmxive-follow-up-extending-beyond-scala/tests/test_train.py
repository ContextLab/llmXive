import json
import os
import pickle
import tempfile
from pathlib import Path
import sys

import pytest
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from train import load_features, prepare_data, train_and_evaluate, save_results

@pytest.fixture
def sample_features(tmp_path):
    """Create a temporary features.json file with valid sample data."""
    features_data = [
        {
            "sample_id": "sample_001",
            "variance": 0.5,
            "entropy": 1.2,
            "skewness": 0.1,
            "kurtosis": 2.8,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.3
        },
        {
            "sample_id": "sample_002",
            "variance": 0.8,
            "entropy": 1.5,
            "skewness": -0.2,
            "kurtosis": 3.1,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.5
        },
        {
            "sample_id": "sample_003",
            "variance": 0.3,
            "entropy": 1.0,
            "skewness": 0.0,
            "kurtosis": 2.5,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.2
        },
        {
            "sample_id": "sample_004",
            "variance": 0.6,
            "entropy": 1.3,
            "skewness": 0.15,
            "kurtosis": 2.9,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.4
        },
        {
            "sample_id": "sample_005",
            "variance": 0.4,
            "entropy": 1.1,
            "skewness": -0.1,
            "kurtosis": 2.7,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.25
        },
        {
            "sample_id": "sample_006",
            "variance": 0.7,
            "entropy": 1.4,
            "skewness": 0.05,
            "kurtosis": 3.0,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.45
        },
        {
            "sample_id": "sample_007",
            "variance": 0.9,
            "entropy": 1.6,
            "skewness": -0.3,
            "kurtosis": 3.2,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.6
        },
        {
            "sample_id": "sample_008",
            "variance": 0.2,
            "entropy": 0.9,
            "skewness": 0.2,
            "kurtosis": 2.4,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.15
        },
        {
            "sample_id": "sample_009",
            "variance": 0.55,
            "entropy": 1.25,
            "skewness": 0.12,
            "kurtosis": 2.85,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.35
        },
        {
            "sample_id": "sample_010",
            "variance": 0.65,
            "entropy": 1.35,
            "skewness": -0.05,
            "kurtosis": 2.95,
            "dominant_eigenvalue": 1.5,
            "fidelity_loss": 0.42
        }
    ]
    features_file = tmp_path / "features.json"
    with open(features_file, 'w') as f:
        json.dump(features_data, f)
    return features_file

def test_load_features_valid(sample_features):
    """Test loading valid features file."""
    data = load_features(sample_features)
    assert len(data) == 10
    assert all('sample_id' in row for row in data)
    assert all('fidelity_loss' in row for row in data)

def test_prepare_data(sample_features):
    """Test data preparation returns correct shapes and types."""
    data = load_features(sample_features)
    X, y, sample_ids = prepare_data(data)
    
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.shape[0] == len(y)
    assert X.shape[1] == 5  # 5 features: variance, entropy, skewness, kurtosis, dominant_eigenvalue
    assert len(sample_ids) == len(y)

def test_train_and_evaluate(sample_features):
    """Test model training and evaluation returns expected outputs."""
    data = load_features(sample_features)
    X, y, sample_ids = prepare_data(data)
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    model, metrics = train_and_evaluate(X, y, MockLogger())
    
    assert model is not None
    assert 'mse' in metrics
    assert 'r2' in metrics
    assert 'mae' in metrics
    assert metrics['mse'] >= 0
    assert metrics['mae'] >= 0
    assert -1 <= metrics['r2'] <= 1  # R2 can be negative for bad models

def test_save_results(tmp_path, sample_features):
    """Test model and metrics are saved correctly."""
    data = load_features(sample_features)
    X, y, sample_ids = prepare_data(data)
    
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    model, metrics = train_and_evaluate(X, y, MockLogger())
    
    model_path = tmp_path / "model.pkl"
    save_results(model, metrics, model_path, MockLogger())
    
    assert model_path.exists()
    
    # Verify model can be loaded
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is not None
    
    # Verify metrics file exists
    metrics_path = model_path.with_suffix('_metrics.json')
    assert metrics_path.exists()
    with open(metrics_path, 'r') as f:
        loaded_metrics = json.load(f)
    assert loaded_metrics == metrics

def test_prepare_data_missing_features(sample_features):
    """Test handling of rows with missing features."""
    data = load_features(sample_features)
    # Corrupt one row
    data[0]['variance'] = None
    
    X, y, sample_ids = prepare_data(data)
    
    # Should skip the corrupted row
    assert len(y) == 9  # One less than original 10

def test_prepare_data_missing_target(sample_features):
    """Test handling of rows with missing target."""
    data = load_features(sample_features)
    # Remove target from one row
    del data[1]['fidelity_loss']
    
    X, y, sample_ids = prepare_data(data)
    
    # Should skip the row without target
    assert len(y) == 9

def test_empty_features(tmp_path):
    """Test error handling for empty features file."""
    empty_file = tmp_path / "empty.json"
    with open(empty_file, 'w') as f:
        json.dump([], f)
    
    with pytest.raises(ValueError, match="Feature file is empty"):
        load_features(empty_file)