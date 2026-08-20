import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from models.train import get_top_features

def test_get_top_features_random_forest():
    """Test feature extraction from a Random Forest model."""
    # Create dummy data
    np.random.seed(42)
    X = pd.DataFrame(np.random.rand(100, 5), columns=['feat_A', 'feat_B', 'feat_C', 'feat_D', 'feat_E'])
    y = pd.Series(np.random.rand(100))
    
    # Train a simple RF
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    # Get top features
    top_features = get_top_features(model, n=3)
    
    assert isinstance(top_features, list)
    assert len(top_features) == 3
    assert all(isinstance(item, tuple) for item in top_features)
    assert all(isinstance(item[0], str) for item in top_features)
    assert all(isinstance(item[1], float) for item in top_features)
    
    # Check sorting (importance should be descending)
    for i in range(len(top_features) - 1):
        assert top_features[i][1] >= top_features[i+1][1]

def test_get_top_features_linear_svr():
    """Test feature extraction from a Linear SVR model."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.rand(100, 3), columns=['x1', 'x2', 'x3'])
    y = pd.Series(X['x1'] * 2 + X['x2'] * 0.5 + np.random.rand(100) * 0.1)
    
    model = SVR(kernel='linear')
    model.fit(X, y)
    
    top_features = get_top_features(model, n=2)
    
    assert isinstance(top_features, list)
    assert len(top_features) == 2
    # Linear SVR uses absolute coefficients as importance
    assert top_features[0][0] == 'x1' # x1 has highest weight
    assert top_features[0][1] >= top_features[1][1]

def test_get_top_features_nonlinear_svr():
    """Test feature extraction from a non-linear SVR (should return empty/warning)."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.rand(100, 2), columns=['a', 'b'])
    y = pd.Series(np.random.rand(100))
    
    model = SVR(kernel='rbf')
    model.fit(X, y)
    
    # Non-linear SVR has no intrinsic importance
    top_features = get_top_features(model, n=5)
    
    assert top_features == []

def test_get_top_features_n_limit():
    """Test that n parameter limits the output correctly."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.rand(100, 10), columns=[f'f{i}' for i in range(10)])
    y = pd.Series(np.random.rand(100))
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    top_5 = get_top_features(model, n=5)
    top_2 = get_top_features(model, n=2)
    
    assert len(top_5) == 5
    assert len(top_2) == 2