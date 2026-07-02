"""
Unit tests for code/analysis.py
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis import aggregate_errors, _clopper_pearson_interval


def test_clopper_pearson_interval_edge_cases():
    """Test Clopper-Pearson interval at boundaries."""
    # 0 successes
    lower, upper = _clopper_pearson_interval(0, 100, 0.05)
    assert lower == 0.0
    assert 0.0 < upper < 1.0

    # 100% successes
    lower, upper = _clopper_pearson_interval(100, 100, 0.05)
    assert 0.0 < lower < 1.0
    assert upper == 1.0

    # 50% successes
    lower, upper = _clopper_pearson_interval(50, 100, 0.05)
    assert 0.0 < lower < 0.5 < upper < 1.0


def test_aggregate_errors_basic():
    """Test basic aggregation of error rates."""
    # Create mock results where p-values are uniformly distributed
    # Under H0, we expect ~5% rejections at alpha=0.05
    np.random.seed(42)
    n_iterations = 1000
    p_values = np.random.uniform(0, 1, n_iterations)

    results = [{'p_value': p} for p in p_values]
    alpha_levels = [0.05]

    df = aggregate_errors(results, alpha_levels)

    assert len(df) == 1
    assert df['alpha'].iloc[0] == 0.05
    assert df['total_trials'].iloc[0] == n_iterations
    assert 0.9 * 0.05 <= df['error_rate'].iloc[0] <= 1.1 * 0.05  # Within 10% of expected


def test_aggregate_errors_with_icc():
    """Test aggregation when ICC values are present."""
    np.random.seed(42)
    results = []
    for icc in [0.0, 0.2, 0.5]:
        for _ in range(100):
            results.append({
                'icc': icc,
                'p_value': np.random.uniform(0, 1)
            })

    alpha_levels = [0.05]
    df = aggregate_errors(results, alpha_levels)

    assert len(df) == 3  # One row per ICC value
    assert set(df['icc']) == {0.0, 0.2, 0.5}


def test_aggregate_errors_empty_list():
    """Test that empty results list raises ValueError."""
    with pytest.raises(ValueError, match="results_list cannot be empty"):
        aggregate_errors([], [0.05])


def test_aggregate_errors_multiple_alphas():
    """Test aggregation with multiple alpha levels."""
    np.random.seed(42)
    p_values = np.random.uniform(0, 1, 500)
    results = [{'p_value': p} for p in p_values]
    alpha_levels = [0.01, 0.05, 0.10]

    df = aggregate_errors(results, alpha_levels)

    assert len(df) == 3
    assert list(df['alpha']) == [0.01, 0.05, 0.10]
    # Error rates should be increasing with alpha
    assert df['error_rate'].iloc[0] <= df['error_rate'].iloc[1] <= df['error_rate'].iloc[2]


def test_clopper_pearson_interval_monotonicity():
    """Test that CI bounds are within [0, 1]."""
    for n in [10, 50, 100, 500]:
        for k in range(n + 1):
            lower, upper = _clopper_pearson_interval(k, n, 0.05)
            assert 0.0 <= lower <= upper <= 1.0