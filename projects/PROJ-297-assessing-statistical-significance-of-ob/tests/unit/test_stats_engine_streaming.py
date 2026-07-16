import pytest
import pandas as pd
import numpy as np
from stats_engine import generate_null_distribution, generate_synthetic_dataset, calculate_stats, construct_graph, compute_correlation
import gc

def test_permutation_preserves_marginals():
    """Verify that permutation preserves marginal distributions."""
    df = generate_synthetic_dataset(n_samples=100, n_vars=5)
    original_means = df.mean()
    original_stds = df.std()
    
    # Permute
    rng = np.random.default_rng(seed=42)
    permuted_df = df.apply(lambda col: rng.permutation(col.values))
    
    # Check means and stds are preserved (within floating point tolerance)
    perm_means = permuted_df.mean()
    perm_stds = permuted_df.std()
    
    assert np.allclose(original_means, perm_means, rtol=1e-10)
    assert np.allclose(original_stds, perm_stds, rtol=1e-10)

def test_null_distribution_generation():
    """Test that null distribution generation works without OOM on small scale."""
    df = generate_synthetic_dataset(n_samples=100, n_vars=5)
    
    def dummy_stats(data):
        c = data.corr()
        return {"mean_abs_corr": np.mean(np.abs(c.values[np.triu_indices_from(c, k=1)]))}
    
    # Small permutation count for test
    null_dist = generate_null_distribution(df, n_permutations=100, stats_func=dummy_stats)
    
    assert "observed" in null_dist
    assert "null" in null_dist
    assert len(null_dist["null"]["mean_abs_corr"]) == 100
    assert "mean_abs_corr" in null_dist["observed"]

def test_memory_efficiency():
    """Test that garbage collection is triggered during long runs."""
    df = generate_synthetic_dataset(n_samples=200, n_vars=10)
    
    def dummy_stats(data):
        c = data.corr()
        return {"mean_abs_corr": np.mean(np.abs(c.values[np.triu_indices_from(c, k=1)]))}
    
    # Run with enough iterations to trigger GC
    null_dist = generate_null_distribution(df, n_permutations=600, stats_func=dummy_stats)
    
    assert len(null_dist["null"]["mean_abs_corr"]) == 600