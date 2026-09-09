"""
Unit tests for analysis functions in code/analyze.py.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from analyze import check_collinearity, analyze_feature_importance

def test_check_collinearity_basic():
    """Test collinearity detection."""
    # Create a dataset with known collinearity
    np.random.seed(42)
    X = pd.DataFrame({
        'f1': np.random.rand(100),
        'f2': np.random.rand(100),
        'f3': np.random.rand(100)
    })
    # Add perfect correlation
    X['f4'] = X['f1'] * 2
    
    collinear_pairs, report = check_collinearity(X, threshold=0.9)
    # f1 and f4 should be detected
    assert len(collinear_pairs) > 0
    assert ('f1', 'f4') in collinear_pairs or ('f4', 'f1') in collinear_pairs

def test_analyze_feature_importance_basic():
    """Test feature importance analysis."""
    X = pd.DataFrame(np.random.rand(100, 5))
    y = pd.Series(np.random.rand(100))
    model = RandomForestRegressor(random_state=42)
    model.fit(X, y)
    
    importance, p_values = analyze_feature_importance(model, X, y, n_permutations=10)
    assert len(importance) == 5
    assert len(p_values) == 5
    assert all(isinstance(p, float) for p in p_values)
