import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression
from models.validate import permutation_test

def test_permutation_test_significance():
    """
    Test that permutation_test returns a low p-value for a model trained on 
    data with a strong signal.
    """
    # Generate data with strong signal
    X, y = make_regression(n_samples=200, n_features=10, noise=0.1, random_state=42)
    X = pd.DataFrame(X)
    y = pd.Series(y)
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    # Run permutation test with fewer iterations for speed
    p_val = permutation_test(model, X, y, n=100, random_state=42)
    
    # With strong signal, p-value should be low (e.g., < 0.1)
    assert p_val < 0.1, f"Expected low p-value for strong signal, got {p_val}"

def test_permutation_test_no_signal():
    """
    Test that permutation_test returns a high p-value for a model trained on 
    random noise (no signal).
    """
    # Generate data with no signal (y is random noise)
    X = np.random.randn(200, 10)
    y = np.random.randn(200)
    X = pd.DataFrame(X)
    y = pd.Series(y)
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    p_val = permutation_test(model, X, y, n=100, random_state=42)
    
    # With no signal, the model should perform similarly on shuffled data
    # so p-value should be high (close to 0.5 or higher)
    assert p_val > 0.05, f"Expected high p-value for no signal, got {p_val}"

def test_permutation_test_small_sample():
    """
    Test that permutation test handles small sample sizes gracefully (T035).
    """
    X = pd.DataFrame(np.random.randn(20, 5))
    y = pd.Series(np.random.randn(20))
    model = RandomForestRegressor(n_estimators=10)
    
    # Should return 1.0 and log a warning
    p_val = permutation_test(model, X, y, n=10, random_state=42)
    
    assert p_val == 1.0, "Expected p-value 1.0 for sample size < 50"
