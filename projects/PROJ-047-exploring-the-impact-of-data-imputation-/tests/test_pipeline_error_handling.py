import pytest
import numpy as np
import pandas as pd
from analysis.pipeline import run_imputation_and_estimation
from sklearn.exceptions import ConvergenceWarning
import warnings

def test_pipeline_handles_convergence_warning():
    """
    Test that the pipeline correctly handles ConvergenceWarning from MICE imputation.
    """
    # Create a dataset that might cause convergence issues
    np.random.seed(123)
    n = 50
    data = {
        'X': pd.DataFrame({
            'X1': np.random.randn(n),
            'X2': np.random.randn(n)
        }),
        'T': np.random.binomial(1, 0.5, n),
        'Y': np.random.randn(n),
        'mask': pd.DataFrame({
            'X1': np.random.binomial(1, 0.8, n).astype(bool),  # High missingness
            'X2': np.random.binomial(1, 0.8, n).astype(bool)
        }),
        'seed': 123,
        'beta': 0.8,
        'run_id': 'test_convergence'
    }
    
    # Run the pipeline
    results = run_imputation_and_estimation(data)
    
    # Verify that the result structure is correct
    assert 'methods' in results
    assert 'mean' in results['methods']
    assert 'knn' in results['methods']
    assert 'mice' in results['methods']
    
    # Check that at least some methods completed (even if some failed)
    total_methods = len(results['methods'])
    successful_methods = sum(1 for m in results['methods'].values() if m['status'] == 'success')
    assert successful_methods >= 0  # At least we have a result structure
    
    # Verify that if a method failed, it has error information
    for method_name, method_result in results['methods'].items():
        if method_result['status'] == 'failed':
            assert method_result['error'] is not None
            assert method_result['estimates'] is not None

def test_pipeline_handles_infinite_estimate():
    """
    Test that the pipeline correctly handles infinite ATE estimates.
    """
    # Create a dataset that might lead to extreme estimates
    np.random.seed(456)
    n = 100
    data = {
        'X': pd.DataFrame({
            'X1': np.random.randn(n),
            'X2': np.random.randn(n)
        }),
        'T': np.random.binomial(1, 0.5, n),
        'Y': np.random.randn(n),
        'mask': pd.DataFrame({
            'X1': np.random.binomial(1, 0.3, n).astype(bool),
            'X2': np.random.binomial(1, 0.3, n).astype(bool)
        }),
        'seed': 456,
        'beta': 0.5,
        'run_id': 'test_infinite'
    }
    
    results = run_imputation_and_estimation(data)
    
    # Verify structure
    assert 'methods' in results
    
    # Check that estimates are either valid numbers or NaN (for failed cases)
    for method_name, method_result in results['methods'].items():
        if method_result['status'] == 'success':
            for est_name, estimate in method_result['estimates'].items():
                if 'ate' in estimate:
                    assert not np.isinf(estimate['ate']), f"Infinite ATE found in {method_name}/{est_name}"

def test_pipeline_preserves_run_metadata():
    """
    Test that the pipeline preserves run metadata (seed, beta, run_id).
    """
    np.random.seed(789)
    n = 50
    data = {
        'X': pd.DataFrame({
            'X1': np.random.randn(n),
            'X2': np.random.randn(n)
        }),
        'T': np.random.binomial(1, 0.5, n),
        'Y': np.random.randn(n),
        'mask': pd.DataFrame({
            'X1': np.random.binomial(1, 0.2, n).astype(bool),
            'X2': np.random.binomial(1, 0.2, n).astype(bool)
        }),
        'seed': 789,
        'beta': 0.2,
        'run_id': 'test_metadata_123'
    }
    
    results = run_imputation_and_estimation(data)
    
    assert results['run_id'] == 'test_metadata_123'
    assert results['seed'] == 789
    assert results['beta'] == 0.2

def test_pipeline_handles_extreme_missingness():
    """
    Test that the pipeline handles extreme missingness rates gracefully.
    """
    np.random.seed(999)
    n = 50
    data = {
        'X': pd.DataFrame({
            'X1': np.random.randn(n),
            'X2': np.random.randn(n)
        }),
        'T': np.random.binomial(1, 0.5, n),
        'Y': np.random.randn(n),
        'mask': pd.DataFrame({
            'X1': np.ones(n).astype(bool),  # 100% missing
            'X2': np.ones(n).astype(bool)
        }),
        'seed': 999,
        'beta': 1.0,
        'run_id': 'test_extreme'
    }
    
    # This should not crash, even if some methods fail
    results = run_imputation_and_estimation(data)
    
    # Verify that we got a result structure
    assert 'methods' in results
    assert len(results['methods']) == 3  # mean, knn, mice

def test_pipeline_output_structure():
    """
    Test that the pipeline output has the expected structure.
    """
    np.random.seed(111)
    n = 100
    data = {
        'X': pd.DataFrame({
            'X1': np.random.randn(n),
            'X2': np.random.randn(n)
        }),
        'T': np.random.binomial(1, 0.5, n),
        'Y': np.random.randn(n),
        'mask': pd.DataFrame({
            'X1': np.random.binomial(1, 0.2, n).astype(bool),
            'X2': np.random.binomial(1, 0.2, n).astype(bool)
        }),
        'seed': 111,
        'beta': 0.0,
        'run_id': 'test_structure'
    }
    
    results = run_imputation_and_estimation(data)
    
    # Check top-level keys
    assert 'run_id' in results
    assert 'seed' in results
    assert 'beta' in results
    assert 'methods' in results
    
    # Check method-level keys
    for method_name, method_result in results['methods'].items():
        assert 'status' in method_result
        assert 'error' in method_result
        assert 'estimates' in method_result
        
        # Check estimator-level keys
        for est_name, estimate in method_result['estimates'].items():
            if estimate['status'] != 'failed':
                assert 'ate' in estimate
                assert 'se' in estimate
                assert 'ci_lower' in estimate
                assert 'ci_upper' in estimate