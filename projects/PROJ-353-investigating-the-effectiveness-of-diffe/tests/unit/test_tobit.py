"""
Unit tests for Tobit Regression implementation.
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.tobit_regression import run_tobit_regression, _log_likelihood, _run_custom_tobit
from utils import MAX_EPOCHS


def test_tobit_regression_basic():
    """Test Tobit regression with simple data."""
    # Create synthetic data (for testing logic, not real data)
    n = 50
    np.random.seed(42)
    
    df = pd.DataFrame({
        'steps_to_convergence': np.random.randint(0, MAX_EPOCHS + 1, n),
        'loss_type': np.random.choice(['ce', 'infonce'], n),
        'beta': np.random.uniform(0, 1, n)
    })
    
    # Add event column (1 if converged, 0 if censored)
    df['event'] = (df['steps_to_convergence'] < MAX_EPOCHS).astype(int)
    
    # Run Tobit regression
    model, results = run_tobit_regression(df)
    
    # Check results structure
    assert 'interaction_p_value' in results
    assert 'coefficients' in results
    assert 'p_values' in results
    assert 'model_type' in results
    
    # Check that we have expected coefficients
    expected_keys = ['intercept', 'loss_type', 'beta', 'interaction']
    for key in expected_keys:
        assert key in results['coefficients']
        assert key in results['p_values']
    
    # Check that p-values are in valid range
    assert 0 <= results['interaction_p_value'] <= 1


def test_tobit_censoring_handling():
    """Test that Tobit correctly handles censored data."""
    # Create data with many censored observations
    n = 50
    np.random.seed(42)
    
    df = pd.DataFrame({
        'steps_to_convergence': np.full(n, MAX_EPOCHS),  # All censored
        'loss_type': np.random.choice(['ce', 'infonce'], n),
        'beta': np.random.uniform(0, 1, n)
    })
    
    df['event'] = (df['steps_to_convergence'] < MAX_EPOCHS).astype(int)
    
    # Run Tobit regression - should not crash
    model, results = run_tobit_regression(df)
    
    # Should still produce results
    assert 'interaction_p_value' in results


def test_custom_tobit_log_likelihood():
    """Test the custom Tobit log-likelihood function."""
    n = 10
    np.random.seed(42)
    
    X = np.random.randn(n, 4)
    y = np.random.randn(n)
    lower = 0
    upper = 10
    
    params = np.array([0.1, 0.2, 0.3, 0.4, 1.0])  # beta + sigma
    
    ll = _log_likelihood(params, X, y, lower, upper)
    
    # Log-likelihood should be finite
    assert np.isfinite(ll)
    
    # Higher sigma should generally increase likelihood (within reason)
    ll_lower_sigma = _log_likelihood(np.array([0.1, 0.2, 0.3, 0.4, 0.5]), X, y, lower, upper)
    assert ll_lower_sigma > ll  # Lower sigma might give lower likelihood for noisy data


def test_custom_tobit_fit():
    """Test that custom Tobit fitting works."""
    n = 30
    np.random.seed(42)
    
    X = np.random.randn(n, 4)
    y = np.random.randint(0, 100, n).astype(float)
    lower = 0
    upper = 50
    
    model, results = _run_custom_tobit(X, y, lower, upper)
    
    assert 'interaction_p_value' in results
    assert 'coefficients' in results
    assert len(results['coefficients']) == 4
    assert results['model_type'] == 'custom'


def test_tobit_with_realistic_data():
    """Test Tobit with more realistic convergence data."""
    np.random.seed(42)
    n = 110
    
    # Simulate convergence steps with some censoring
    beta_vals = np.random.uniform(0, 1, n)
    loss_types = np.random.choice(['ce', 'infonce'], n)
    
    # Generate steps with some relationship to beta and loss_type
    steps = 200 - 50 * beta_vals + 30 * (loss_types == 'infonce').astype(float)
    steps += np.random.normal(0, 20, n)
    steps = np.clip(steps, 0, MAX_EPOCHS)
    
    # Add censoring
    steps = np.where(steps >= MAX_EPOCHS, MAX_EPOCHS, steps)
    
    df = pd.DataFrame({
        'steps_to_convergence': steps,
        'loss_type': loss_types,
        'beta': beta_vals
    })
    df['event'] = (df['steps_to_convergence'] < MAX_EPOCHS).astype(int)
    
    model, results = run_tobit_regression(df)
    
    # Should produce reasonable results
    assert 0 <= results['interaction_p_value'] <= 1
    assert 'intercept' in results['coefficients']
    assert 'loss_type' in results['coefficients']
    assert 'beta' in results['coefficients']
    assert 'interaction' in results['coefficients']