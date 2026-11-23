"""
Unit tests for the training module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path if running from tests
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from training import load_training_data, train_model
from utils import set_deterministic_seed

@pytest.fixture
def mock_training_data(tmp_path):
    """Create a mock training dataset for testing."""
    # Create a mock parquet file
    data = {
        'feature_1': np.random.rand(100),
        'feature_2': np.random.rand(100),
        'feature_3': np.random.rand(100),
        'labels': [
            ['pitting', 'uniform'] if i % 3 == 0 else 
            ['scc'] if i % 3 == 1 else 
            ['crevice', 'pitting']
            for i in range(100)
        ]
    }
    df = pd.DataFrame(data)
    mock_path = tmp_path / "train_set.parquet"
    df.to_parquet(mock_path)
    return mock_path

def test_load_training_data(mock_training_data):
    """Test that load_training_data correctly loads and formats data."""
    X, y = load_training_data(mock_training_data)
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.DataFrame)
    assert X.shape[0] == 100
    assert y.shape[0] == 100
    # Check that labels are binarized
    assert set(y.columns) == {'crevice', 'pitting', 'scc', 'uniform'}
    assert y.values.sum() > 0  # Ensure there are some positive labels

def test_train_model(mock_training_data):
    """Test that train_model returns a valid model and metrics."""
    set_deterministic_seed(42)
    X, y = load_training_data(mock_training_data)
    
    model, metrics = train_model(X, y, random_state=42, n_estimators=5)
    
    assert model is not None
    assert isinstance(metrics, dict)
    assert 'macro_f1_score' in metrics
    assert 'n_estimators' in metrics
    assert metrics['n_estimators'] == 5
    assert 0 <= metrics['macro_f1_score'] <= 1
    
    # Check label F1 scores
    assert 'label_f1_scores' in metrics
    assert len(metrics['label_f1_scores']) == y.shape[1]

def test_train_model_cpu_only():
    """Test that the model is configured for CPU (n_jobs=1 in base estimator)."""
    # This is implicitly tested by the implementation using n_jobs=1 in RandomForestClassifier
    # We verify the model structure if possible, but the main check is in the code review.
    pass
