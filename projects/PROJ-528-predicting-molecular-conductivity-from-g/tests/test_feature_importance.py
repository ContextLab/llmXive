import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.feature_importance import (
    compute_feature_importance,
    extract_tree_importance,
    run_feature_importance_analysis
)

@pytest.fixture
def mock_model():
    """Create a mock model with feature_importances_"""
    model = Mock()
    model.feature_importances_ = np.array([0.3, 0.2, 0.15, 0.1, 0.05, 0.05, 0.05, 0.05])
    model.predict = Mock(return_value=np.array([1, 2, 3, 4, 5]))
    return model

@pytest.fixture
def mock_X():
    """Create mock feature DataFrame"""
    return pd.DataFrame({
        'feature_a': np.random.randn(100),
        'feature_b': np.random.randn(100),
        'feature_c': np.random.randn(100),
        'feature_d': np.random.randn(100),
        'feature_e': np.random.randn(100),
        'feature_f': np.random.randn(100),
        'feature_g': np.random.randn(100),
        'feature_h': np.random.randn(100)
    })

@pytest.fixture
def mock_y():
    """Create mock target Series"""
    return pd.Series(np.random.randn(100))

def test_compute_feature_importance_returns_dataframe(mock_model, mock_X, mock_y):
    """Test that compute_feature_importance returns a DataFrame with correct columns"""
    importance_df, summary = compute_feature_importance(mock_model, mock_X, mock_y, n_repeats=2)
    
    assert isinstance(importance_df, pd.DataFrame)
    assert 'feature' in importance_df.columns
    assert 'importance_mean' in importance_df.columns
    assert 'importance_std' in importance_df.columns
    assert 'z_score' in importance_df.columns
    assert 'p_value' in importance_df.columns
    
    # Check that we have the right number of features
    assert len(importance_df) == len(mock_X.columns)
    
    # Check that it's sorted by importance
    assert importance_df['importance_mean'].is_monotonic_decreasing

def test_compute_feature_importance_summary(mock_model, mock_X, mock_y):
    """Test that summary contains expected keys"""
    _, summary = compute_feature_importance(mock_model, mock_X, mock_y, n_repeats=2)
    
    assert 'total_features' in summary
    assert 'significant_features_at_0.05' in summary
    assert 'top_feature' in summary
    assert 'mean_importance' in summary
    assert 'std_importance' in summary

def test_extract_tree_importance(mock_model, mock_X):
    """Test that extract_tree_importance returns correct DataFrame"""
    importance_df = extract_tree_importance(mock_model, mock_X)
    
    assert isinstance(importance_df, pd.DataFrame)
    assert 'feature' in importance_df.columns
    assert 'tree_importance' in importance_df.columns
    assert len(importance_df) == len(mock_X.columns)
    assert importance_df['tree_importance'].sum() == pytest.approx(1.0, rel=0.1)

def test_extract_tree_importance_no_attribute():
    """Test behavior when model has no feature_importances_"""
    model = Mock()
    delattr(model, 'feature_importances_')
    
    X = pd.DataFrame({'a': [1, 2, 3]})
    result = extract_tree_importance(model, X)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

@patch('code.feature_importance.load_processed_data')
@patch('code.feature_importance.iterative_vif_retrain')
@patch('code.feature_importance.compute_feature_importance')
def test_run_feature_importance_analysis(mock_compute, mock_retrain, mock_load, mock_X, mock_y, mock_model):
    """Test the full pipeline with mocked dependencies"""
    # Setup mocks
    mock_load.return_value = (mock_X, mock_y, list(mock_X.columns), 'target')
    mock_retrain.return_value = (mock_model, mock_X, mock_y, ['excluded_feat'], [])
    mock_compute.return_value = (
        pd.DataFrame({
            'feature': ['a', 'b'],
            'importance_mean': [0.5, 0.3],
            'importance_std': [0.1, 0.05],
            'z_score': [5.0, 6.0],
            'p_value': [0.01, 0.02]
        }),
        {'total_features': 2, 'top_feature': 'a'}
    )
    
    # Run the function
    importance_df, summary = run_feature_importance_analysis(
        model_type='random_forest',
        output_path='data/processed/test_importance.csv',
        summary_path='data/processed/test_summary.json'
    )
    
    # Verify calls
    mock_load.assert_called_once()
    mock_retrain.assert_called_once()
    mock_compute.assert_called_once()
    
    # Verify output
    assert isinstance(importance_df, pd.DataFrame)
    assert 'total_features' in summary

def test_permutation_importance_with_realistic_data():
    """Test permutation importance with more realistic data distribution"""
    from sklearn.ensemble import RandomForestRegressor
    
    # Create realistic data
    np.random.seed(42)
    n_samples = 200
    X_real = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'feature_4': np.random.randn(n_samples),
    })
    
    # Create target with known relationship
    y_real = 2 * X_real['feature_1'] + 1.5 * X_real['feature_2'] + np.random.randn(n_samples) * 0.5
    
    # Train a simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_real, y_real)
    
    # Compute importance
    importance_df, summary = compute_feature_importance(model, X_real, y_real, n_repeats=5)
    
    # feature_1 should have highest importance
    assert importance_df.iloc[0]['feature'] == 'feature_1'
    
    # feature_3 and feature_4 should have low importance
    assert importance_df.iloc[-1]['feature'] in ['feature_3', 'feature_4']
    assert importance_df.iloc[-2]['feature'] in ['feature_3', 'feature_4']