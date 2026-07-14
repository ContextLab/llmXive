"""
Unit tests for the analyzer module.

Tests aggregation logic, bootstrap CI calculation, and stability metrics.
"""
import pytest
import pandas as pd
import numpy as np
from analyzer import compute_bootstrap_ci, aggregate_results, calculate_stability_variance, load_simulation_results

@pytest.fixture
def sample_data():
    """Create sample simulation data for testing."""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        data.append({
            'sample_size': 50,
            'distribution': 'normal',
            'test_type': 't_test',
            'rejected': np.random.binomial(1, 0.05),  # Simulate Type I error
            'effect_size': 0.0
        })
        data.append({
            'sample_size': 100,
            'distribution': 'normal',
            'test_type': 't_test',
            'rejected': np.random.binomial(1, 0.05),
            'effect_size': 0.0
        })
    return pd.DataFrame(data)

def test_compute_bootstrap_ci_basic():
    """Test basic bootstrap CI calculation with known data."""
    # Data with mean 0.5
    data = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    lower, upper = compute_bootstrap_ci(data, confidence=0.95, n_bootstraps=100)
    
    assert 0.4 <= lower <= 0.6, f"Lower bound {lower} out of expected range"
    assert 0.4 <= upper <= 0.6, f"Upper bound {upper} out of expected range"
    assert lower <= upper, "Lower bound should be less than or equal to upper bound"

def test_compute_bootstrap_ci_empty():
    """Test bootstrap CI with empty data."""
    data = np.array([])
    lower, upper = compute_bootstrap_ci(data)
    
    assert lower == 0.0
    assert upper == 0.0

def test_aggregate_results_basic(sample_data):
    """Test basic aggregation of simulation results."""
    result = aggregate_results(sample_data)
    
    assert 'error_rate' in result.columns
    assert 'ci_lower' in result.columns
    assert 'ci_upper' in result.columns
    assert len(result) > 0

def test_calculate_stability_variance(sample_data):
    """Test stability variance calculation."""
    # First aggregate the data
    agg_df = aggregate_results(sample_data)
    
    # Calculate stability variance
    stability = calculate_stability_variance(agg_df)
    
    # Should have entries for the test types present
    assert isinstance(stability, dict)
    # The variance should be non-negative
    for key, val in stability.items():
        assert val >= 0, f"Variance for {key} is negative: {val}"