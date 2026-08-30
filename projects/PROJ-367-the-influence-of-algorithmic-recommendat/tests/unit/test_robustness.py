"""
Unit tests for code/robustness.py.

Tests permutation test logic and E-value calculation.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from robustness import residual_permutation_test, calculate_e_value


def test_residual_permutation_test_basic():
    """Test that the permutation test runs and returns expected structure."""
    # Create simple mock data
    np.random.seed(42)
    n = 50
    X = np.random.randn(n, 2)
    y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(n) * 0.1

    # Run a small number of iterations for speed
    result = residual_permutation_test(X, y, n_iterations=10)

    assert "observed_statistic" in result
    assert "null_distribution" in result
    assert "p_value" in result
    assert "ci_lower" in result
    assert "ci_upper" in result

    # Check dimensions
    assert len(result["null_distribution"]) == 10
    assert isinstance(result["p_value"], float)
    assert 0.0 <= result["p_value"] <= 1.0


def test_residual_permutation_test_determinism():
    """Test that the permutation test is deterministic with a fixed seed."""
    np.random.seed(123)
    n = 30
    X = np.random.randn(n, 1)
    y = X[:, 0] * 1.5 + np.random.randn(n) * 0.5

    result1 = residual_permutation_test(X, y, n_iterations=5, random_seed=42)
    result2 = residual_permutation_test(X, y, n_iterations=5, random_seed=42)

    # Results should be identical
    assert np.isclose(result1["observed_statistic"], result2["observed_statistic"])
    assert np.allclose(result1["null_distribution"], result2["null_distribution"])
    assert np.isclose(result1["p_value"], result2["p_value"])


def test_residual_permutation_test_null_case():
    """Test that permutation test detects no effect when there is none."""
    np.random.seed(999)
    n = 100
    # X and y are independent
    X = np.random.randn(n, 1)
    y = np.random.randn(n)

    result = residual_permutation_test(X, y, n_iterations=100, random_seed=7)

    # When there is no true effect, the observed statistic should be within
    # the null distribution, leading to a non-significant p-value (typically > 0.05)
    # Note: With only 100 iterations, there is variance, but it should generally be high
    assert result["p_value"] > 0.01  # Very lenient check for small sample


def test_calculate_e_value():
    """Test E-value calculation formula."""
    # E-value = OR + sqrt(OR * (OR - 1))
    # For OR = 1 (no effect), E-value should be 1
    e_val = calculate_e_value(1.0)
    assert np.isclose(e_val, 1.0, atol=1e-5)

    # For OR = 2, E-value = 2 + sqrt(2 * 1) = 2 + 1.414... = 3.414...
    e_val = calculate_e_value(2.0)
    expected = 2.0 + np.sqrt(2.0 * (2.0 - 1.0))
    assert np.isclose(e_val, expected, atol=1e-5)

    # For OR = 1.5
    # E = 1.5 + sqrt(1.5 * 0.5) = 1.5 + sqrt(0.75) = 1.5 + 0.866 = 2.366
    e_val = calculate_e_value(1.5)
    expected = 1.5 + np.sqrt(1.5 * 0.5)
    assert np.isclose(e_val, expected, atol=1e-5)

    # For OR = 1.1
    # E = 1.1 + sqrt(1.1 * 0.1) = 1.1 + sqrt(0.11) ≈ 1.1 + 0.33166 = 1.43166
    e_val = calculate_e_value(1.1)
    expected = 1.1 + np.sqrt(1.1 * 0.1)
    assert np.isclose(e_val, expected, atol=1e-5)


def test_calculate_e_value_edge_cases():
    """Test E-value calculation with edge cases."""
    # OR slightly above 1
    e_val = calculate_e_value(1.0001)
    expected = 1.0001 + np.sqrt(1.0001 * 0.0001)
    assert np.isclose(e_val, expected, atol=1e-5)

    # OR = 3
    e_val = calculate_e_value(3.0)
    expected = 3.0 + np.sqrt(3.0 * 2.0)
    assert np.isclose(e_val, expected, atol=1e-5)