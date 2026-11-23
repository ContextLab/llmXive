"""
Integration tests for the robustness analysis suite.

Verifies that the permutation test and sensitivity analysis run end-to-end.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from robustness import run_robustness_suite, residual_permutation_test


@pytest.fixture
def mock_model_data():
    """Create mock data for modeling and robustness tests."""
    np.random.seed(42)
    n = 100
    # Simulate some features and a target
    X = np.random.randn(n, 3)
    # True relationship: y = 2*X0 + 0.5*X1 + noise
    y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n) * 0.1
    return X, y


def test_run_robustness_suite(mock_model_data):
    """Test the full robustness suite execution."""
    X, y = mock_model_data
    
    # Run the suite with a small number of iterations for speed
    # In production, this would be 1000+
    results = run_robustness_suite(X, y, n_permutations=20)
    
    assert "permutation_test" in results
    assert "sensitivity_analysis" in results
    
    # Check permutation test results
    p_test = results["permutation_test"]
    assert "observed_statistic" in p_test
    assert "p_value" in p_test
    assert "ci_lower" in p_test
    assert "ci_upper" in p_test
    
    # Check sensitivity analysis results
    sens = results["sensitivity_analysis"]
    assert isinstance(sens, dict)
    # The keys should be the thresholds tested
    assert "0.01" in sens or 0.01 in sens # Check if keys are strings or floats


def test_permutation_test_consistency(mock_model_data):
    """Test that permutation test results are consistent across runs (with fixed seed)."""
    X, y = mock_model_data
    
    # Run twice with same seed
    result1 = residual_permutation_test(X, y, n_iterations=50, random_seed=123)
    result2 = residual_permutation_test(X, y, n_iterations=50, random_seed=123)
    
    # Results should be identical
    assert result1["observed_statistic"] == result2["observed_statistic"]
    assert np.array_equal(result1["null_distribution"], result2["null_distribution"])
    assert result1["p_value"] == result2["p_value"]