import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from importance import validate_correlation, rank_features, calculate_vif

def test_validate_correlation():
    """Test correlation calculation between two sets of importances."""
    rf_importances = {'a': 0.5, 'b': 0.3, 'c': 0.2}
    perm_importances = {'a': 0.45, 'b': 0.35, 'c': 0.25}
    
    r = validate_correlation(rf_importances, perm_importances)
    
    # Check that r is a float and within [-1, 1]
    assert isinstance(r, float)
    assert -1.0 <= r <= 1.0
    # Since the values are highly correlated, r should be high (e.g., > 0.9)
    assert r > 0.9

def test_rank_features():
    """Test feature ranking logic."""
    rf_importances = {'a': 0.5, 'b': 0.3, 'c': 0.2}
    perm_importances = {'a': 0.45, 'b': 0.35, 'c': 0.25}
    
    ranked = rank_features(rf_importances, perm_importances, top_n=2)
    
    assert len(ranked) == 2
    assert ranked[0]['feature'] == 'a'
    assert ranked[0]['rank'] == 1
    assert ranked[1]['feature'] == 'b'
    assert ranked[1]['rank'] == 2

def test_calculate_vif():
    """Test VIF calculation."""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame({
        'f1': np.random.randn(n_samples),
        'f2': np.random.randn(n_samples),
        'f3': np.random.randn(n_samples)
    })
    feature_names = ['f1', 'f2', 'f3']
    
    vif_scores = calculate_vif(X, feature_names)
    
    assert 'f1' in vif_scores
    assert 'f2' in vif_scores
    assert 'f3' in vif_scores
    # VIF should be >= 1.0
    for v in vif_scores.values():
        assert v >= 1.0
