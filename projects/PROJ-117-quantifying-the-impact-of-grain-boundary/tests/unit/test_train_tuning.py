"""
Unit tests for train_tuning module.
"""
import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Import module under test
import code.train_tuning as train_tuning

@pytest.fixture
def sample_data():
    """Create sample DataFrame for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'feature1': np.random.rand(n_samples),
        'feature2': np.random.rand(n_samples),
        'feature3': np.random.rand(n_samples),
        'diffusivity': np.random.rand(n_samples) * 10
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create necessary subdirectories
        (tmpdir / "data" / "processed").mkdir(parents=True)
        (tmpdir / "models").mkdir(parents=True)
        (tmpdir / "artifacts" / "reports").mkdir(parents=True)
        yield tmpdir

@pytest.fixture
def mock_project_root(temp_dirs):
    """Mock PROJECT_ROOT to point to temp directory."""
    with patch.object(train_tuning, 'PROJECT_ROOT', temp_dirs):
        with patch.object(train_tuning, 'DATA_DIR', temp_dirs / "data"):
            with patch.object(train_tuning, 'PROCESSED_DIR', temp_dirs / "data" / "processed"):
                with patch.object(train_tuning, 'MODELS_DIR', temp_dirs / "models"):
                    with patch.object(train_tuning, 'ARTIFACTS_DIR', temp_dirs / "artifacts"):
                        with patch.object(train_tuning, 'REPORTS_DIR', temp_dirs / "artifacts" / "reports"):
                            yield temp_dirs

def test_load_and_prepare_data(mock_project_root, sample_data, tmp_path):
    """Test data loading and preparation."""
    # Write sample data to parquet
    input_file = mock_project_root / "data" / "processed" / "cleaned_dataset.parquet"
    sample_data.to_parquet(input_file)
    
    # Load and prepare
    X, y = train_tuning.load_and_prepare_data()
    
    assert X.shape[0] == sample_data.shape[0]
    assert y.shape[0] == sample_data.shape[0]
    assert 'feature1' in X.columns
    assert 'diffusivity' not in X.columns
    assert y.name == 'diffusivity'

def test_split_data(mock_project_root, sample_data, tmp_path):
    """Test 70/15/15 split and index saving."""
    # Write sample data
    input_file = mock_project_root / "data" / "processed" / "cleaned_dataset.parquet"
    sample_data.to_parquet(input_file)
    
    # Load and split
    X, y = train_tuning.load_and_prepare_data()
    X_train, X_val, X_test, y_train, y_val, y_test = train_tuning.split_data(X, y)
    
    # Check sizes
    assert X_train.shape[0] == int(len(X) * 0.70)
    assert X_val.shape[0] == int(len(X) * 0.15)
    assert X_test.shape[0] == int(len(X) * 0.15)
    
    # Check indices file was created
    split_file = mock_project_root / "data" / "processed" / "split_indices.pkl"
    assert split_file.exists()
    
    # Check indices content
    with open(split_file, 'rb') as f:
        indices = pickle.load(f)
    
    assert 'train' in indices
    assert 'val' in indices
    assert 'test' in indices
    assert len(indices['train']) == X_train.shape[0]

def test_tune_hyperparameters(mock_project_root, sample_data, tmp_path):
    """Test hyperparameter tuning."""
    # Write sample data
    input_file = mock_project_root / "data" / "processed" / "cleaned_dataset.parquet"
    sample_data.to_parquet(input_file)
    
    # Load and split
    X, y = train_tuning.load_and_prepare_data()
    X_train, X_val, X_test, y_train, y_val, y_test = train_tuning.split_data(X, y)
    
    # Tune (with reduced iterations for speed)
    with patch.object(train_tuning, 'PARAM_DISTRIBUTION', {
        'max_depth': [3, 5],
        'learning_rate': [0.1],
        'n_estimators': [10]
    }):
        best_params = train_tuning.tune_hyperparameters(X_train, y_train, X_val, y_val)
    
    assert 'max_depth' in best_params
    assert 'learning_rate' in best_params
    assert 'n_estimators' in best_params
    
    # Check params file
    params_file = mock_project_root / "models" / "best_params.json"
    assert params_file.exists()
    
    with open(params_file, 'r') as f:
        saved_params = json.load(f)
    
    assert saved_params == best_params

def test_measure_compute_metrics(mock_project_root, sample_data, tmp_path):
    """Test compute metrics measurement."""
    start_time = 0.0
    metrics = train_tuning.measure_compute_metrics(start_time)
    
    assert 'runtime_seconds' in metrics
    assert 'peak_memory_mb' in metrics
    assert metrics['runtime_seconds'] >= 0
    assert metrics['peak_memory_mb'] > 0
    
    # Check file
    metrics_file = mock_project_root / "artifacts" / "reports" / "compute_metrics.json"
    assert metrics_file.exists()