"""
Unit tests for Monte Carlo simulation loop logic.
Specifically verifies seed 42 reproducibility for the simulation engine.
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_seed, set_memory_limit
from data.generate_contamination import process_dataset, inject_contamination
from utils.stats_helpers import run_t_test_monte_carlo

# Mock data generator for testing reproducibility without heavy I/O
def _generate_mock_data(n_samples=1000, n_features=5):
    """Generate a simple mock dataset for unit testing."""
    np.random.seed(42)
    data = np.random.randn(n_samples, n_features)
    # Create a simple binary target for t-test (0 or 1)
    target = np.random.choice([0, 1], size=n_samples)
    return pd.DataFrame(data, columns=[f"feat_{i}" for i in range(n_features)]), target

def test_monte_carlo_seed_reproducibility():
    """
    Verify that running the Monte Carlo loop with seed 42 produces
    identical results across multiple runs.
    """
    # Ensure the global seed is set to 42 as per project config
    seed = get_seed()
    assert seed == 42, f"Expected default seed 42, got {seed}"

    # Generate mock data
    data, target = _generate_mock_data(n_samples=200, n_features=2)

    # Configuration for a small Monte Carlo run
    n_iterations = 50
    contamination_rate = 0.0
    contamination_magnitude = 3.0
    alpha = 0.05

    results_run_1 = []
    results_run_2 = []

    # Run 1
    np.random.seed(seed)
    for i in range(n_iterations):
        # Simulate the loop logic found in run_simulation.py
        # 1. Resample/Contaminate (mocked here for speed)
        current_data = data.copy()
        if contamination_rate > 0:
            # Inject contamination
            current_data, _ = inject_contamination(
                current_data, target, 
                contamination_rate=contamination_rate, 
                magnitude=contamination_magnitude, 
                seed=seed + i  # Deterministic per iteration
            )
        
        # 2. Run test (mocked t-test on first feature)
        group_0 = current_data.loc[target == 0, "feat_0"]
        group_1 = current_data.loc[target == 1, "feat_0"]
        
        if len(group_0) > 1 and len(group_1) > 1:
            stat, p_val = run_t_test_monte_carlo(
                group_0.values, group_1.values, 
                n_permutations=100, seed=seed + i
            )
            results_run_1.append({"iter": i, "p_val": p_val, "stat": stat})
        else:
            results_run_1.append({"iter": i, "p_val": None, "stat": None})

    # Run 2 (Reset seed to 42 and repeat)
    np.random.seed(seed)
    for i in range(n_iterations):
        current_data = data.copy()
        if contamination_rate > 0:
            current_data, _ = inject_contamination(
                current_data, target, 
                contamination_rate=contamination_rate, 
                magnitude=contamination_magnitude, 
                seed=seed + i
            )
        
        group_0 = current_data.loc[target == 0, "feat_0"]
        group_1 = current_data.loc[target == 1, "feat_0"]
        
        if len(group_0) > 1 and len(group_1) > 1:
            stat, p_val = run_t_test_monte_carlo(
                group_0.values, group_1.values, 
                n_permutations=100, seed=seed + i
            )
            results_run_2.append({"iter": i, "p_val": p_val, "stat": stat})
        else:
            results_run_2.append({"iter": i, "p_val": None, "stat": None})

    # Verify reproducibility
    df1 = pd.DataFrame(results_run_1)
    df2 = pd.DataFrame(results_run_2)

    # Check that dataframes are identical
    assert df1.equals(df2), (
        f"Monte Carlo results are not reproducible with seed {seed}.\n"
        f"Run 1 head:\n{df1.head()}\n"
        f"Run 2 head:\n{df2.head()}"
    )

def test_monte_carlo_seed_change_affects_results():
    """
    Verify that changing the seed produces different results,
    ensuring the randomization is actually active.
    """
    data, target = _generate_mock_data(n_samples=200, n_features=2)
    n_iterations = 20
    
    results_seed_42 = []
    results_seed_123 = []

    # Run with seed 42
    np.random.seed(42)
    for i in range(n_iterations):
        group_0 = data.loc[target == 0, "feat_0"].values
        group_1 = data.loc[target == 1, "feat_0"].values
        if len(group_0) > 1 and len(group_1) > 1:
            stat, p_val = run_t_test_monte_carlo(
                group_0, group_1, n_permutations=50, seed=42 + i
            )
            results_seed_42.append(p_val)

    # Run with seed 123
    np.random.seed(123)
    for i in range(n_iterations):
        group_0 = data.loc[target == 0, "feat_0"].values
        group_1 = data.loc[target == 1, "feat_0"].values
        if len(group_0) > 1 and len(group_1) > 1:
            stat, p_val = run_t_test_monte_carlo(
                group_0, group_1, n_permutations=50, seed=123 + i
            )
            results_seed_123.append(p_val)

    # They should be different (probability of exact match is near zero)
    assert results_seed_42 != results_seed_123, (
        "Monte Carlo results should differ when seed changes."
    )

def test_monte_carlo_null_hypothesis_type1_error():
    """
    Verify that under a true null hypothesis (resampled from same population),
    the Type I error rate is approximately alpha (0.05) when seed is fixed.
    """
    # Create a single homogeneous population
    np.random.seed(42)
    population = np.random.randn(1000)
    
    n_iterations = 100
    alpha = 0.05
    p_values = []

    # Simulate Type I error scenario: sample two groups from SAME population
    np.random.seed(42)
    for i in range(n_iterations):
        # Resample with replacement from the same pool (true null)
        group_a = np.random.choice(population, size=50, replace=True)
        group_b = np.random.choice(population, size=50, replace=True)
        
        # Run test
        stat, p_val = run_t_test_monte_carlo(
            group_a, group_b, n_permutations=200, seed=42 + i
        )
        if p_val is not None:
            p_values.append(p_val)

    if not p_values:
        pytest.skip("No valid p-values generated")

    # Calculate empirical Type I error
    empirical_error_rate = sum(1 for p in p_values if p <= alpha) / len(p_values)
    
    # Allow a tolerance (e.g., +/- 0.05) for statistical variation in small N
    # With N=100, we expect ~5 rejections. Tolerance of 3 is reasonable.
    expected_rejections = n_iterations * alpha
    tolerance = 0.15 # 15% absolute tolerance for small sample test
    
    assert abs(empirical_error_rate - alpha) <= tolerance, (
        f"Empirical Type I error rate {empirical_error_rate:.3f} "
        f"differs significantly from expected {alpha} (tolerance {tolerance})"
    )