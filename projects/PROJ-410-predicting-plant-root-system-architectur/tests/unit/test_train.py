"""
Unit tests for Random Forest training functionality in code/train.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from train import (
    load_data,
    prepare_features_targets,
    train_random_forest,
    train_rf_for_condition
)

@pytest.fixture
def sample_data():
    """Create sample training data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'accession': [f'Col-{i}' for i in range(n_samples)],
        'nutrient_condition': ['low_n'] * 50 + ['high_n'] * 50,
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'root_length': np.random.randn(n_samples) * 10 + 50
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

def test_prepare_features_targets(sample_data):
    """Test feature and target extraction from DataFrame."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    target_col = 'root_length'
    
    X, y = prepare_features_targets(sample_data, feature_cols, target_col)
    
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.shape == (100, 3)
    assert y.shape == (100,)
    assert np.allclose(X[0], sample_data[feature_cols].iloc[0].values)
    assert y[0] == sample_data[root_length].iloc[0]

def test_train_random_forest_basic(sample_data):
    """Test basic Random Forest training without hyperparameter search."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    target_col = 'root_length'
    
    X_train, y_train = prepare_features_targets(sample_data, feature_cols, target_col)
    
    model, metrics = train_random_forest(
        X_train, y_train,
        hyperparams={'n_estimators': [10], 'max_depth': [5]},
        cv_folds=3
    )
    
    assert model is not None
    assert 'best_params' in metrics
    assert 'best_cv_score' in metrics
    assert 'cv_r2_mean' in metrics
    assert 'model_type' in metrics
    assert metrics['model_type'] == 'RandomForest'
    assert metrics['best_params']['n_estimators'] == 10
    assert metrics['best_params']['max_depth'] == 5

def test_train_random_forest_with_validation(sample_data, temp_dir):
    """Test Random Forest training with validation set."""
    # Split data for training and validation
    train_data = sample_data.iloc[:80]
    val_data = sample_data.iloc[80:]
    
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    target_col = 'root_length'
    
    X_train, y_train = prepare_features_targets(train_data, feature_cols, target_col)
    X_val, y_val = prepare_features_targets(val_data, feature_cols, target_col)
    
    model, metrics = train_random_forest(
        X_train, y_train,
        X_val, y_val,
        hyperparams={'n_estimators': [10], 'max_depth': [5]},
        cv_folds=3
    )
    
    assert 'val_r2' in metrics
    assert 'val_mae' in metrics
    assert 0 <= metrics['val_r2'] <= 1  # R² should be between 0 and 1
    assert metrics['val_mae'] >= 0  # MAE should be non-negative

def test_train_rf_for_condition(sample_data, temp_dir):
    """Test training RF for a specific nutrient condition."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    target_col = 'root_length'
    
    result = train_rf_for_condition(
        sample_data, None, 'low_n',
        feature_cols, target_col, temp_dir,
        hyperparams={'n_estimators': [10], 'max_depth': [5]}
    )
    
    assert result['status'] == 'success'
    assert result['condition'] == 'low_n'
    assert 'model_path' in result
    assert 'metrics' in result
    assert Path(result['model_path']).exists()
    
    # Verify metrics file exists
    metrics_path = Path(result['model_path']).with_suffix('.json')
    assert metrics_path.exists()
    
    with open(metrics_path, 'r') as f:
        saved_metrics = json.load(f)
    
    assert 'best_params' in saved_metrics
    assert saved_metrics['nutrient_condition'] == 'low_n'

def test_train_rf_no_data(temp_dir):
    """Test training RF when no data exists for condition."""
    empty_df = pd.DataFrame({
        'accession': [],
        'nutrient_condition': [],
        'feature_1': [],
        'root_length': []
    })
    
    feature_cols = ['feature_1']
    target_col = 'root_length'
    
    result = train_rf_for_condition(
        empty_df, None, 'low_n',
        feature_cols, target_col, temp_dir
    )
    
    assert result['status'] == 'skipped'
    assert result['reason'] == 'No data'
    assert result['condition'] == 'low_n'

def test_prepare_features_targets_mismatch():
    """Test error handling for mismatched feature columns."""
    df = pd.DataFrame({
        'feature_1': [1, 2, 3],
        'target': [4, 5, 6]
    })
    
    with pytest.raises(KeyError):
        prepare_features_targets(df, ['nonexistent_feature'], 'target')