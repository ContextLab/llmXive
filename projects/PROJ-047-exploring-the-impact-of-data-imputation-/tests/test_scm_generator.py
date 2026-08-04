import pytest
import numpy as np
from simulation.scm_generator import regenerate_ground_truth, generate_scm, check_collinearity

def test_regenerate_ground_truth():
    """
    Test that regenerate_ground_truth returns the expected values for seed=42, beta=0.5.
    According to the specification, tau_true should be 0.5 (hardcoded constant)
    and beta should be 0.5 exactly.
    """
    seed = 42
    beta = 0.5
    
    tau_true, returned_beta = regenerate_ground_truth(seed, beta)
    
    assert tau_true == 0.5, f"Expected tau_true=0.5, got {tau_true}"
    assert returned_beta == 0.5, f"Expected beta=0.5, got {returned_beta}"

def test_regenerate_ground_truth_deterministic():
    """
    Test that regenerate_ground_truth is deterministic for the same inputs.
    """
    seed = 123
    beta = 0.8
    
    result1 = regenerate_ground_truth(seed, beta)
    result2 = regenerate_ground_truth(seed, beta)
    
    assert result1 == result2, "regenerate_ground_truth should be deterministic"

def test_generate_scm_basic():
    """
    Test basic functionality of generate_scm.
    """
    seed = 42
    n = 100
    tau_true = 0.5
    
    dataset = generate_scm(seed, n, tau_true)
    
    assert dataset.X.shape == (n,), f"Expected X shape ({n},), got {dataset.X.shape}"
    assert dataset.T.shape == (n,), f"Expected T shape ({n},), got {dataset.T.shape}"
    assert dataset.Y.shape == (n,), f"Expected Y shape ({n},), got {dataset.Y.shape}"
    assert dataset.ground_truth_ate == tau_true
    assert dataset.seed == seed

def test_check_collinearity_no_collinearity():
    """
    Test that check_collinearity returns False for uncorrelated data.
    """
    rng = np.random.default_rng(42)
    X = rng.normal(0, 1, (100, 3))
    
    assert not check_collinearity(X), "Should not detect collinearity in random data"

def test_check_collinearity_with_collinearity():
    """
    Test that check_collinearity returns True for highly correlated data.
    """
    rng = np.random.default_rng(42)
    X1 = rng.normal(0, 1, 100)
    X2 = X1 + rng.normal(0, 0.01, 100)  # Nearly identical
    X3 = rng.normal(0, 1, 100)
    X = np.column_stack([X1, X2, X3])
    
    assert check_collinearity(X), "Should detect collinearity in correlated data"
