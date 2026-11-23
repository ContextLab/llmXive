import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold
from code.modeling import (
    train_gradient_boosting, 
    train_random_forest, 
    compute_shap_values, 
    compute_permutation_importance, 
    rank_features, 
    calculate_spearman_correlation
)

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    X = np.random.randn(n_samples, n_features)
    y = X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n_samples) * 0.1
    return X, y, ['f1', 'f2', 'f3', 'f4', 'f5']

def test_nested_cv_gradient_boosting(sample_data):
    """Test Gradient Boosting with nested CV (no data leakage)."""
    X, y, feature_names = sample_data
    
    model, metrics = train_gradient_boosting(X, y, cv_folds=3)
    
    assert isinstance(model, GradientBoostingRegressor)
    assert 'mean_r2' in metrics
    assert 'mean_rmse' in metrics
    assert metrics['mean_r2'] <= 1.0
    assert metrics['mean_rmse'] >= 0
    # Basic sanity check: R2 should be positive for this synthetic data
    assert metrics['mean_r2'] > 0.1

def test_nested_cv_random_forest(sample_data):
    """Test Random Forest with nested CV (no data leakage)."""
    X, y, feature_names = sample_data
    
    model, metrics = train_random_forest(X, y, cv_folds=3)
    
    assert isinstance(model, RandomForestRegressor)
    assert 'mean_r2' in metrics
    assert 'mean_rmse' in metrics
    assert metrics['mean_r2'] <= 1.0
    assert metrics['mean_rmse'] >= 0
    assert metrics['mean_r2'] > 0.1

def test_shap_values_computation(sample_data):
    """Test SHAP value calculation and ranking stability."""
    X, y, feature_names = sample_data
    
    # Train a simple model first
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X, y)
    
    shap_values, explainer = compute_shap_values(model, X, feature_names)
    
    assert shap_values.shape == X.shape
    assert explainer is not None
    assert np.all(np.isfinite(shap_values))

def test_permutation_importance(sample_data):
    """Test permutation importance calculation."""
    X, y, feature_names = sample_data
    
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X, y)
    
    perm_importance = compute_permutation_importance(model, X, y, feature_names)
    
    assert len(perm_importance) == len(feature_names)
    assert np.all(np.isfinite(perm_importance))

def test_rank_features(sample_data):
    """Test feature ranking functionality."""
    X, y, feature_names = sample_data
    
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X, y)
    
    shap_values, _ = compute_shap_values(model, X, feature_names)
    perm_importance = compute_permutation_importance(model, X, y, feature_names)
    
    ranking_df = rank_features(shap_values, perm_importance)
    
    assert 'shap_rank' in ranking_df.columns
    assert 'perm_rank' in ranking_df.columns
    assert len(ranking_df) == len(feature_names)
    assert ranking_df['shap_rank'].min() == 1
    assert ranking_df['shap_rank'].max() == len(feature_names)

def test_spearman_correlation_stability(sample_data):
    """Test Spearman correlation between SHAP and permutation rankings."""
    X, y, feature_names = sample_data
    
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X, y)
    
    shap_values, _ = compute_shap_values(model, X, feature_names)
    perm_importance = compute_permutation_importance(model, X, y, feature_names)
    
    ranking_df = rank_features(shap_values, perm_importance)
    
    corr = calculate_spearman_correlation(
        ranking_df['shap_rank'].values,
        ranking_df['perm_rank'].values
    )
    
    assert -1.0 <= corr <= 1.0
    # For consistent models, correlation should be reasonably high
    assert corr >= 0.5