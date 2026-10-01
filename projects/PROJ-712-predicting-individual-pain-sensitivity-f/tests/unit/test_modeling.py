import pytest
import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import KFold
from scipy.stats import pearsonr

from modeling import calculate_observed_metric, run_global_permutation_test, run_bootstrap_ci

@pytest.fixture
def dummy_data():
    np.random.seed(42)
    n_samples = 50
    n_features = 30
    X = np.random.randn(n_samples, n_features)
    # Create a synthetic target with some correlation to first feature
    y = X[:, 0] * 0.5 + np.random.randn(n_samples) * 0.5
    return X, y

def test_calculate_observed_metric(dummy_data):
    X, y = dummy_data
    r, std, mae, coefs = calculate_observed_metric(X, y, seed=42, k_outer=5, k_inner=3)
    
    assert isinstance(r, float)
    assert isinstance(std, float)
    assert isinstance(mae, float)
    assert isinstance(coefs, np.ndarray)
    assert len(coefs) == X.shape[1]
    assert not np.isnan(r)
    assert not np.isnan(std)
    assert not np.isnan(mae)

def test_run_global_permutation_test(dummy_data):
    X, y = dummy_data
    null_dist, p_value = run_global_permutation_test(X, y, n_permutations=10, seed=42)
    
    assert isinstance(null_dist, np.ndarray)
    assert len(null_dist) == 10
    assert isinstance(p_value, float)
    assert 0.0 <= p_value <= 1.0

def test_run_bootstrap_ci(dummy_data):
    X, y = dummy_data
    lower, upper = run_bootstrap_ci(X, y, n_bootstraps=10, seed=42)
    
    assert isinstance(lower, float)
    assert isinstance(upper, float)
    assert lower <= upper
    assert not np.isnan(lower)
    assert not np.isnan(upper)
