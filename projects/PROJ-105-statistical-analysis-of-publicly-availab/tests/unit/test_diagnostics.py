import pytest
import numpy as np
from scipy import stats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from diagnostics import (
    estimate_hill_index,
    compute_hill_stability_curve,
    find_optimal_k_stability,
    calculate_hill_confidence_interval,
    run_hill_stability_analysis
)

def test_hill_estimator_basic():
    """Test Hill estimator on a known Pareto distribution."""
    # Generate Pareto data (alpha=2.0)
    np.random.seed(42)
    n = 10000
    data = stats.pareto.rvs(2.0, size=n)
    
    k = 100
    alpha_hat = estimate_hill_index(data, k)
    
    # Should be close to 2.0
    assert 1.5 < alpha_hat < 2.5, f"Alpha {alpha_hat} too far from 2.0"

def test_hill_stability_curve():
    """Test that stability curve returns arrays of correct length."""
    np.random.seed(42)
    data = stats.pareto.rvs(2.0, size=5000)
    
    k_min = 10
    k_max_ratio = 0.1
    k_values, alphas = compute_hill_stability_curve(data, k_min=k_min, k_max_ratio=k_max_ratio)
    
    assert len(k_values) == len(alphas)
    assert k_values[0] >= k_min
    assert k_values[-1] <= int(len(data) * k_max_ratio)

def test_find_optimal_k():
    """Test variance minimization logic."""
    # Create a curve where variance is minimal at a specific k
    k_values = np.arange(10, 100)
    # Simulate alphas: high variance at start, low in middle, high at end
    alphas = np.ones_like(k_values, dtype=float)
    alphas[:10] += np.random.uniform(-0.5, 0.5, 10)
    alphas[10:50] += np.random.uniform(-0.05, 0.05, 40) # Stable region
    alphas[50:] += np.random.uniform(-0.5, 0.5, 50)
    
    optimal_k, min_var = find_optimal_k_stability(k_values, alphas, window_size=10)
    
    # Optimal K should be in the stable region
    assert 10 <= optimal_k <= 50, f"Optimal K {optimal_k} outside stable region"
    assert min_var < 0.01, f"Min variance {min_var} too high"

def test_hill_confidence_interval():
    """Test CI calculation."""
    np.random.seed(42)
    data = stats.pareto.rvs(2.0, size=1000)
    k = 100
    alpha = estimate_hill_index(data, k)
    
    lower, upper = calculate_hill_confidence_interval(data, k, alpha)
    
    assert lower < alpha < upper
    assert (upper - lower) > 0

def test_run_hill_stability_analysis():
    """Integration test for full analysis."""
    np.random.seed(42)
    data = stats.pareto.rvs(2.0, size=5000)
    x_min = 1.0
    
    results = run_hill_stability_analysis(data, x_min, window_size=10, k_max_ratio=0.1)
    
    assert "summary" in results
    assert "curve" in results
    assert results["summary"]["estimated_alpha"] > 1.0
    assert results["summary"]["estimated_alpha"] < 3.0