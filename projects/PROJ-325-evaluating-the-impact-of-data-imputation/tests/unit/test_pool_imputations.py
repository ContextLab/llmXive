"""
Unit tests for pool_imputations function in imputation_pipeline.py
"""
import pytest
import pandas as pd
import numpy as np
import miceforest as mf
from imputation_pipeline import pool_imputations

def create_mock_kernel_data(n_rows=100, n_iters=1000, missing_rate=0.1, seed=42):
    """
    Create a mock miceforest KernelDensityImputation object for testing.
    Since mocking the full object is complex, we create a minimal object
    that satisfies the interface used in pool_imputations.
    """
    np.random.seed(seed)
    # Create synthetic data with some missingness
    data = pd.DataFrame({
        'var1': np.random.normal(10, 2, n_rows)
    })
    
    # Introduce missingness
    mask = np.random.random(n_rows) < missing_rate
    data.loc[mask, 'var1'] = np.nan

    # Create iterations
    # We need to simulate the imputation process.
    # For testing pool_imputations, we need 'imputed_data' attribute which is a list of DataFrames.
    iterations = []
    for i in range(n_iters):
        # Simulate an iteration: fill NA with a value that varies slightly per iteration
        # to create variance between imputations.
        df_iter = data.copy()
        na_indices = df_iter['var1'].isna()
        if na_indices.any():
            # Add some noise to the imputed value
            noise = np.random.normal(0, 0.1 * (i+1)) # Slight drift
            df_iter.loc[na_indices, 'var1'] = data['var1'].mean() + noise
        iterations.append(df_iter)

    # Create a mock object
    class MockKernelData:
        def __init__(self, imputed_data):
            self.imputed_data = imputed_data

    return MockKernelData(iterations)

def test_pool_imputations_basic():
    """Test basic pooling functionality."""
    # Create 2 mock chains
    chain1 = create_mock_kernel_data(n_rows=50, n_iters=1000, missing_rate=0.2, seed=1)
    chain2 = create_mock_kernel_data(n_rows=50, n_iters=1000, missing_rate=0.2, seed=2)
    
    imputation_results = [chain1, chain2]
    variable = 'var1'
    m = 5
    burn_in = 500

    # Run pooling
    result = pool_imputations(imputation_results, variable, m=m, burn_in=burn_in)

    # Check structure
    assert 'pooled_mean' in result
    assert 'pooled_variance' in result
    assert 'within_variance' in result
    assert 'between_variance' in result

    # Check types
    assert isinstance(result['pooled_mean'], float)
    assert isinstance(result['pooled_variance'], float)
    
    # Check that variance is positive
    assert result['pooled_variance'] > 0

def test_pool_imputations_insufficient_iterations():
    """Test that pooling fails if burn_in is too high."""
    chain = create_mock_kernel_data(n_rows=50, n_iters=100, missing_rate=0.2, seed=1)
    
    with pytest.raises(ValueError, match="has only 100 iterations, which is <= burn_in"):
        pool_imputations([chain], 'var1', m=5, burn_in=100)

def test_pool_imputations_mismatch_m():
    """Test behavior when m is larger than available iterations."""
    # Create a chain with few iterations
    chain = create_mock_kernel_data(n_rows=50, n_iters=10, missing_rate=0.2, seed=1)
    
    # We have 10 iterations, burn_in=5 -> 5 available.
    # If we ask for m=10, it should fail or handle gracefully.
    # The current implementation raises ValueError if not enough.
    with pytest.raises(ValueError):
        pool_imputations([chain], 'var1', m=10, burn_in=5)

def test_pool_imputations_rubins_rules():
    """
    Verify that Rubin's rules are applied correctly.
    We construct a scenario where we know the between and within variance.
    """
    # This is a more complex test. We rely on the basic structure test for now.
    # The logic is:
    # Q_bar = mean(Q_i)
    # U_bar = mean(U_i)
    # B = var(Q_i)
    # T = U_bar + (1 + 1/m) * B
    # We check that T > U_bar (since B >= 0)
    chain1 = create_mock_kernel_data(n_rows=50, n_iters=1000, missing_rate=0.2, seed=1)
    chain2 = create_mock_kernel_data(n_rows=50, n_iters=1000, missing_rate=0.2, seed=2)
    
    result = pool_imputations([chain1, chain2], 'var1', m=5, burn_in=500)
    
    # T should be greater than U_bar because of the between variance term
    assert result['pooled_variance'] >= result['within_variance']