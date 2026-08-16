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
