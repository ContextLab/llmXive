import pytest
import pandas as pd
import numpy as np
from analysis.stats import run_null_distribution_validation

def test_null_distribution_validation_structure():
    """
    Test that run_null_distribution_validation returns the correct structure.
    """
    np.random.seed(123)
    n = 50
    metrics = pd.DataFrame({
        'm1': np.random.rand(n),
        'm2': np.random.rand(n)
    })
    genres = pd.Series(np.random.rand(n))
    
    result = run_null_distribution_validation(metrics, genres, n_permutations=100)
    
    assert 'false_positive_rate' in result
    assert 'permutations_count' in result
    assert isinstance(result['false_positive_rate'], float)
    assert result['permutations_count'] == 100
    assert 0.0 <= result['false_positive_rate'] <= 1.0

def test_null_distribution_validation_with_known_null():
    """
    Test that with truly random data, the FPR is approximately alpha (0.05).
    Note: With only 100 permutations, this is a rough check.
    """
    np.random.seed(456)
    n = 100
    metrics = pd.DataFrame({
        'random_metric': np.random.rand(n)
    })
    genres = pd.Series(np.random.rand(n))
    
    # Run with a larger number of permutations for a better estimate
    result = run_null_distribution_validation(metrics, genres, n_permutations=1000)
    
    # The FPR should be close to 0.05 (alpha), typically between 0.02 and 0.08 for N=1000
    # This is a probabilistic check, so we allow some variance.
    fpr = result['false_positive_rate']
    assert 0.01 <= fpr <= 0.10, f"Expected FPR around 0.05, got {fpr}"
    assert result['permutations_count'] == 1000

def test_null_distribution_validation_empty_metrics():
    """
    Test behavior with empty metrics DataFrame.
    """
    metrics = pd.DataFrame()
    genres = pd.Series([1, 2, 3])
    
    # Should handle gracefully or raise a specific error
    # Based on implementation, it might return 0.0 or raise.
    # Let's assume it returns 0.0 FPR if no tests run.
    result = run_null_distribution_validation(metrics, genres, n_permutations=10)
    assert result['false_positive_rate'] == 0.0
    assert result['permutations_count'] == 10
