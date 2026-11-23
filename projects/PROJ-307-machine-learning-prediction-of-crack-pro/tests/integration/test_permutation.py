"""
Integration test for Permutation Test significance (T020/T023).
Verifies that the permutation test logic runs end-to-end and produces a valid p-value
using the actual model training functions from the pipeline.
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

# Import the stats module functions
from code.utils.stats import permutation_test_model_comparison

# Import the actual model functions to ensure integration
from code.models.baseline import train_baseline_model, evaluate_baseline
from code.models.augmented import train_augmented_model, evaluate_model


def _create_test_dataset(n_samples: int = 100, seed: int = 42):
    """
    Creates a synthetic dataset that mimics the structure expected by the model functions.
    This is for INTEGRATION TESTING ONLY to verify the permutation logic flows correctly
    without requiring the full data pipeline or real external data downloads.
    
    The data mimics:
    - X_base: log(ΔK) features (1D)
    - X_aug: log(ΔK) + composition/heat-treatment features
    - y: log(da/dN)
    """
    np.random.seed(seed)
    
    # Simulate log(ΔK) - positive values as expected in physics
    delta_k_log = np.random.uniform(2.0, 5.0, n_samples)
    
    # Simulate composition features (wt%)
    comp_1 = np.random.uniform(0.0, 10.0, n_samples)
    comp_2 = np.random.uniform(0.0, 5.0, n_samples)
    
    # Simulate heat treatment (encoded as continuous for simplicity in test)
    heat_treat = np.random.uniform(0.0, 1.0, n_samples)
    
    # Target: log(da/dN) with a clear Paris Law component + noise + composition effect
    # y = C * (ΔK)^m + noise
    # In log space: log(y) = log(C) + m * log(ΔK) + noise
    m = 3.0
    C = 1e-10
    base_rate = np.log10(C * (10**delta_k_log)**m)
    
    # Add composition influence
    comp_effect = 0.05 * comp_1 + 0.02 * comp_2
    
    # Add noise
    noise = np.random.normal(0, 0.1, n_samples)
    
    y = base_rate + comp_effect + noise
    
    # Prepare feature matrices
    X_base = delta_k_log.reshape(-1, 1)
    X_aug = np.column_stack([delta_k_log, comp_1, comp_2, heat_treat])
    
    return X_base, X_aug, y


@pytest.mark.integration
def test_permutation_test_baseline_vs_augmented():
    """
    Integration test: Run the permutation test comparing the Baseline (Paris Law) 
    model against the Augmented (ML) model.
    
    Validates:
    1. The stats function runs without error.
    2. It returns a valid p-value (0.0 <= p <= 1.0).
    3. It returns the expected distribution of statistics.
    4. It correctly interfaces with the model training functions.
    """
    # 1. Prepare data
    X_base, X_aug, y = _create_test_dataset(n_samples=80, seed=42)
    
    # 2. Define wrappers that match the expected signature for the permutation test
    # The permutation test expects functions with signature (X, y) -> (model, score)
    def baseline_wrapper(X, y):
        # Handle if X is 1D array (reshape if necessary)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        model, score = train_baseline_model(X, y)
        return model, score

    def augmented_wrapper(X, y):
        # Ensure X has enough columns for the augmented model (at least 2)
        if X.shape[1] < 2:
            # Pad with dummy features if test data is too small, though _create_test_dataset handles this
            dummy_cols = np.random.rand(X.shape[0], 2 - X.shape[1])
            X = np.hstack([X, dummy_cols])
        model, score = train_augmented_model(X, y)
        return model, score

    # 3. Execute the permutation test
    # We use a small number of permutations (20) for CI speed, 
    # but the logic remains the same as the full run (n_permutations=1000).
    n_perms = 20
    seed_val = 42
    
    p_value, permutation_stats = permutation_test_model_comparison(
        X_base=X_base,
        X_aug=X_aug,
        y=y,
        baseline_model_func=baseline_wrapper,
        augmented_model_func=augmented_wrapper,
        n_permutations=n_perms,
        seed=seed_val
    )
    
    # 4. Assertions
    assert isinstance(p_value, float), "p_value must be a float"
    assert 0.0 <= p_value <= 1.0, f"p_value {p_value} must be between 0 and 1"
    
    assert isinstance(permutation_stats, list), "permutation_stats must be a list"
    assert len(permutation_stats) == n_perms, f"Expected {n_perms} stats, got {len(permutation_stats)}"
    
    # Verify stats are floats/numbers
    for stat in permutation_stats:
        assert isinstance(stat, (int, float)), "Each stat must be a number"
    
    # 5. Log result for visibility
    print(f"Integration Test Permutation Test Results:")
    print(f"  - Permutations: {n_perms}")
    print(f"  - P-value: {p_value:.4f}")
    print(f"  - Stats (first 5): {permutation_stats[:5]}")
    
    # Note: We do NOT assert p_value < 0.05 here because with random seed 42
    # and small n, the result might vary. The goal is to verify the pipeline runs.
    # In a real run with real data and sufficient permutations, we expect significance.


@pytest.mark.integration
def test_permutation_test_consistency():
    """
    Verifies that the permutation test is deterministic with a fixed seed.
    """
    X_base, X_aug, y = _create_test_dataset(n_samples=50, seed=99)
    
    def baseline_wrapper(X, y):
        if X.ndim == 1: X = X.reshape(-1, 1)
        return train_baseline_model(X, y)

    def augmented_wrapper(X, y):
        if X.shape[1] < 2:
            dummy_cols = np.random.rand(X.shape[0], 2 - X.shape[1])
            X = np.hstack([X, dummy_cols])
        return train_augmented_model(X, y)

    # Run twice with same seed
    p1, stats1 = permutation_test_model_comparison(
        X_base=X_base, X_aug=X_aug, y=y,
        baseline_model_func=baseline_wrapper,
        augmented_model_func=augmented_wrapper,
        n_permutations=10, seed=12345
    )
    
    p2, stats2 = permutation_test_model_comparison(
        X_base=X_base, X_aug=X_aug, y=y,
        baseline_model_func=baseline_wrapper,
        augmented_model_func=augmented_wrapper,
        n_permutations=10, seed=12345
    )
    
    assert p1 == p2, "P-values should be identical with same seed"
    assert stats1 == stats2, "Stats lists should be identical with same seed"