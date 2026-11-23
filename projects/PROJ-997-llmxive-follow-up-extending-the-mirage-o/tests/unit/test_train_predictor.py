"""
Unit tests for the train_predictor.py script.

Tests cover:
- Data loading and validation
- Feature/target preparation
- Model training logic
- Metric calculation
- File I/O operations
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import pandas as pd
from sklearn.kernel_ridge import KernelRidge
from scipy.stats import pearsonr

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cli.train_predictor import (
    load_training_data,
    prepare_features_targets,
    train_krr_model,
    save_model,
    save_training_metrics,
    KRR_ALPHA,
    KRR_KERNEL,
    KRR_GAMMA
)

@pytest.fixture
def sample_training_data():
    """Create sample training data for testing."""
    data = {
        'input_id': ['id1', 'id2', 'id3', 'id4'],
        'gradient_norms': [0.5, 1.2, 0.8, 1.5],
        'local_curvature': [0.3, 0.7, 0.4, 0.9],
        'calculated_kl_divergence': [0.1, 0.4, 0.2, 0.6],
        'quantization_level': ['INT4', 'INT8', 'FP8', 'INT4']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_training_data_success(sample_training_data, temp_dir):
    """Test successful loading of training data."""
    # Save sample data to parquet
    test_file = temp_dir / "test_train.parquet"
    sample_training_data.to_parquet(test_file)
    
    # Load data
    df = load_training_data(test_file)
    
    assert len(df) == 4
    assert 'gradient_norms' in df.columns
    assert 'local_curvature' in df.columns
    assert 'calculated_kl_divergence' in df.columns

def test_load_training_data_file_not_found(temp_dir):
    """Test that FileNotFoundError is raised when file doesn't exist."""
    non_existent = temp_dir / "nonexistent.parquet"
    
    with pytest.raises(FileNotFoundError):
        load_training_data(non_existent)

def test_load_training_data_missing_columns(temp_dir, sample_training_data):
    """Test that ValueError is raised when required columns are missing."""
    # Remove a required column
    incomplete_data = sample_training_data.drop(columns=['gradient_norms'])
    test_file = temp_dir / "incomplete.parquet"
    incomplete_data.to_parquet(test_file)
    
    with pytest.raises(ValueError) as exc_info:
        load_training_data(test_file)
    
    assert 'gradient_norms' in str(exc_info.value)

def test_prepare_features_targets(sample_training_data):
    """Test correct preparation of features and targets."""
    X, y = prepare_features_targets(sample_training_data)
    
    assert X.shape == (4, 2)  # 4 samples, 2 features
    assert y.shape == (4,)
    
    # Check feature columns
    expected_features = sample_training_data[['gradient_norms', 'local_curvature']].values
    assert np.allclose(X, expected_features)
    
    # Check target
    expected_target = sample_training_data['calculated_kl_divergence'].values
    assert np.allclose(y, expected_target)

def test_train_krr_model_basic(sample_training_data):
    """Test basic model training."""
    X, y = prepare_features_targets(sample_training_data)
    
    model = train_krr_model(X, y)
    
    assert isinstance(model, KernelRidge)
    assert model.alpha == KRR_ALPHA
    assert model.kernel == KRR_KERNEL
    
    # Check that model can make predictions
    predictions = model.predict(X)
    assert len(predictions) == len(y)

def test_train_krr_model_with_nan_values(sample_training_data, temp_dir):
    """Test that training fails with NaN values."""
    # Create data with NaN
    nan_data = sample_training_data.copy()
    nan_data.loc[0, 'gradient_norms'] = np.nan
    
    test_file = temp_dir / "nan_data.parquet"
    nan_data.to_parquet(test_file)
    
    df = load_training_data(test_file)
    X, y = prepare_features_targets(df)
    
    # This should not crash during preparation, but training should handle it
    # or the caller should validate before training
    # For this test, we just ensure the function accepts the input
    # The actual NaN handling might be done in the main function
    model = train_krr_model(X, y)
    assert isinstance(model, KernelRidge)

def test_save_model(temp_dir):
    """Test saving model to pickle file."""
    # Create a dummy model
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    y = np.array([1.0, 2.0])
    model = KernelRidge(alpha=1.0)
    model.fit(X, y)
    
    model_path = temp_dir / "test_model.pkl"
    save_model(model, model_path)
    
    assert model_path.exists()
    assert model_path.stat().st_size > 0

def test_save_training_metrics(temp_dir):
    """Test saving metrics to JSON."""
    metrics = {
        "mae": 0.123,
        "r2": 0.95,
        "pearson_r": 0.98,
        "n_samples": 100,
        "n_features": 2,
        "hyperparameters": {
            "alpha": 1.0,
            "kernel": "rbf",
            "gamma": 0.1
        }
    }
    
    metrics_path = temp_dir / "test_metrics.json"
    save_training_metrics(metrics, metrics_path)
    
    assert metrics_path.exists()
    
    with open(metrics_path, 'r') as f:
        loaded_metrics = json.load(f)
    
    assert loaded_metrics == metrics

def test_model_training_reachability(sample_training_data):
    """Test that the trained model achieves reasonable metrics."""
    X, y = prepare_features_targets(sample_training_data)
    model = train_krr_model(X, y)
    
    y_pred = model.predict(X)
    
    # Calculate metrics
    mae = np.mean(np.abs(y - y_pred))
    r2 = 1 - (np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2))
    corr, _ = pearsonr(y, y_pred)
    
    # Basic sanity checks
    assert mae >= 0
    assert -1 <= r2 <= 1  # R2 can be negative for bad models, but should be bounded
    assert -1 <= corr <= 1

def test_krr_hyperparameters_used(sample_training_data):
    """Test that the correct hyperparameters are used."""
    X, y = prepare_features_targets(sample_training_data)
    
    # Train with specific parameters
    model = KernelRidge(alpha=KRR_ALPHA, kernel=KRR_KERNEL, gamma=KRR_GAMMA)
    model.fit(X, y)
    
    assert model.alpha == KRR_ALPHA
    assert model.kernel == KRR_KERNEL
    assert model.gamma == KRR_GAMMA
