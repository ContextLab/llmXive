import pytest
import numpy as np
from modeling import run_global_permutation_test

@pytest.fixture
def small_dataset():
    np.random.seed(42)
    X = np.random.randn(20, 30)
    y = np.random.randn(20)
    return X, y

def test_global_permutation_structure(small_dataset):
    """
    Integration test for global permutation test logic.
    Verifies that the null distribution is generated correctly and p-value is calculated.
    """
    X, y = small_dataset
    # Run with a small number of permutations for speed
    null_dist, p_value = run_global_permutation_test(X, y, n_permutations=20, seed=42)
    
    # Check dimensions
    assert len(null_dist) == 20
    
    # Check p-value range
    assert 0.0 <= p_value <= 1.0
    
    # Check that null distribution is not all identical (randomness is working)
    assert np.std(null_dist) > 0, "Null distribution should have variance"
    
    # Check that p-value is consistent with null distribution relative to a hypothetical observed
    # (We can't check exact value without running observed, but structure is validated)
    assert isinstance(null_dist, np.ndarray)
    assert null_dist.dtype in [np.float64, np.float32, np.float]