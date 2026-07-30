"""
Unit tests for the model training pipeline (T015).
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.train import (
    load_processed_features,
    prepare_data,
    train_ridge,
    train_lasso,
    train_xgboost,
    main
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    data = {
        'clip_id': [f'clip_{i}' for i in range(n_samples)],
        'feature_0': np.random.randn(n_samples),
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'feature_4': np.random.randn(n_samples),
        'expert_score': np.random.randn(n_samples) * 0.5 + 0.3
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_data(sample_data):
    """Create a temporary processed data file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_data.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_prepare_data(sample_data):
    """Test data preparation and scaling."""
    feature_cols = ['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4']
    X_train, X_test, y_train, y_test, scaler = prepare_data(sample_data, feature_cols)
    
    assert X_train.shape[1] == len(feature_cols)
    assert X_test.shape[1] == len(feature_cols)
    assert len(y_train) + len(y_test) == len(sample_data)
    assert isinstance(scaler, type(None) or hasattr(scaler, 'transform'))
    
    # Check that scaling was applied (mean should be close to 0)
    X_train_scaled = scaler.transform(X_train)
    assert np.allclose(np.mean(X_train_scaled, axis=0), 0, atol=1e-6)

def test_train_ridge(sample_data):
    """Test Ridge regression training."""
    feature_cols = ['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4']
    X_train, X_test, y_train, y_test, scaler = prepare_data(sample_data, feature_cols)
    
    results = train_ridge(X_train, X_test, y_train, y_test, alphas=[0.1, 1.0])
    
    assert 'model' in results
    assert 'type' in results
    assert results['type'] == 'Ridge'
    assert 'best_alpha' in results
    assert 'cv_results' in results
    assert 'test_metrics' in results
    assert 'r2' in results['test_metrics']
    assert 'rmse' in results['test_metrics']
    assert 'feature_importance' in results
    assert len(results['feature_importance']) == len(feature_cols)

def test_train_lasso(sample_data):
    """Test Lasso regression training."""
    feature_cols = ['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4']
    X_train, X_test, y_train, y_test, scaler = prepare_data(sample_data, feature_cols)
    
    results = train_lasso(X_train, X_test, y_train, y_test, alphas=[0.01, 0.1])
    
    assert 'model' in results
    assert 'type' in results
    assert results['type'] == 'Lasso'
    assert 'best_alpha' in results
    assert 'cv_results' in results
    assert 'test_metrics' in results
    assert 'r2' in results['test_metrics']
    assert 'rmse' in results['test_metrics']
    assert 'feature_importance' in results
    assert 'non_zero_features' in results

def test_train_xgboost(sample_data):
    """Test XGBoost training."""
    feature_cols = ['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4']
    X_train, X_test, y_train, y_test, scaler = prepare_data(sample_data, feature_cols)
    
    results = train_xgboost(X_train, X_test, y_train, y_test)
    
    assert 'model' in results
    assert 'type' in results
    assert results['type'] == 'XGBoost'
    assert 'params' in results
    assert 'test_metrics' in results
    assert 'r2' in results['test_metrics']
    assert 'rmse' in results['test_metrics']
    assert 'feature_importance' in results

@patch('src.models.train.load_processed_features')
@patch('src.models.train.get_project_root')
@patch('src.models.train.get_reports_root')
@patch('src.models.train.write_json')
def test_main(mock_write_json, mock_get_reports, mock_get_project, mock_load_features, sample_data):
    """Test the main training pipeline."""
    mock_load_features.return_value = sample_data
    mock_get_reports.return_value = tempfile.gettempdir()
    mock_get_project.return_value = tempfile.gettempdir()
    
    result = main()
    
    assert result is not None
    assert 'models' in result
    assert 'best_model' in result
    assert 'Ridge' in result['models']
    assert 'Lasso' in result['models']
    assert 'XGBoost' in result['models']
    mock_write_json.assert_called_once()
