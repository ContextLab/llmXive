import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from train import train_xgboost_nested_cv, train_linear_baseline, stratified_split, get_feature_columns

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'd_band_center': np.random.randn(n),
        'adsorption_energy': np.random.randn(n),
        'composition': ['A'] * n,
        'surface_facet': ['001'] * n,
        'energy_change': np.random.randn(n)
    }
    # Add some other dummy features
    for i in range(3):
        data[f'feature_{i}'] = np.random.randn(n)
    return pd.DataFrame(data)

def test_train_linear_baseline(sample_data):
    """Test that linear baseline trains and produces predictions."""
    feature_cols = ['d_band_center', 'adsorption_energy']
    X_train = sample_data[feature_cols].values[:80]
    y_train = sample_data['energy_change'].values[:80]
    X_test = sample_data[feature_cols].values[80:]
    y_test = sample_data['energy_change'].values[80:]
    
    result = train_linear_baseline(X_train, y_train, X_test, y_test)
    
    assert 'model' in result
    assert 'r2' in result
    assert 'mae' in result
    assert 'predictions' in result
    assert len(result['predictions']) == len(y_test)
    assert isinstance(result['r2'], float)
    assert isinstance(result['mae'], float)

def test_xgboost_nested_cv(sample_data):
    """Test that XGBoost nested CV runs and returns results."""
    feature_cols = get_feature_columns(sample_data)
    X = sample_data[feature_cols].values
    y = sample_data['energy_change'].values
    
    # Split manually for test
    X_train, X_test = X[:80], X[80:]
    y_train, y_test = y[:80], y[80:]
    
    # Mock the GridSearch to speed up test and verify parameter selection logic
    with patch('train.GridSearchCV') as mock_grid:
        mock_model = MagicMock()
        mock_model.predict.return_value = np.random.randn(len(y_test))
        mock_grid_instance = MagicMock()
        mock_grid_instance.best_estimator_ = mock_model
        mock_grid_instance.best_params_ = {'max_depth': 3, 'learning_rate': 0.1, 'n_estimators': 100}
        mock_grid_instance.best_score_ = 0.5
        mock_grid.return_value = mock_grid_instance
        
        result = train_xgboost_nested_cv(X_train, y_train, X_test, y_test)
        
        assert 'model' in result
        assert 'best_params' in result
        assert 'test_r2' in result
        assert 'test_mae' in result
        assert 'predictions' in result
        
        # Verify GridSearch was called with correct params
        mock_grid.assert_called_once()
        call_kwargs = mock_grid.call_args[1]
        
        # Verify the specific hyperparameter grid defined in T026
        assert 'param_grid' in call_kwargs
        param_grid = call_kwargs['param_grid']
        assert param_grid['max_depth'] == [3, 5, 7]
        assert param_grid['learning_rate'] == [0.01, 0.1]
        assert param_grid['n_estimators'] == [100, 200]
        
        # Verify cross-validation folds (Outer loop 5-fold as per T026)
        # Note: The mock intercepts the GridSearch, but we verify the call signature
        # The implementation should pass cv=5 to GridSearchCV for the inner loop
        assert 'cv' in call_kwargs
        assert call_kwargs['cv'] == 5

def test_stratified_split(sample_data):
    """Test that split function works correctly."""
    train_df, test_df = stratified_split(sample_data, test_size=0.2)
    assert len(train_df) + len(test_df) == len(sample_data)
    assert len(test_df) == int(len(sample_data) * 0.2)
    assert 'energy_change' in train_df.columns
    assert 'energy_change' in test_df.columns