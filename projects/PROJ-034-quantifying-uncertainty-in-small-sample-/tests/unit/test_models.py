"""
Unit tests for OLS model implementation.
"""
import pytest
import numpy as np
from code.models.ols import OLSModel, fit_ols_and_get_intervals

def test_ols_basic_fit():
    """Test basic OLS fitting with known data."""
    # Simple linear relationship: y = 2x + 1 + noise
    np.random.seed(42)
    n = 100
    X = np.random.randn(n, 1)
    true_beta = np.array([1.0, 2.0]) # intercept=1, slope=2
    y = X @ true_beta[1:] + true_beta[0] + np.random.randn(n) * 0.1

    model = OLSModel()
    model.fit(X, y)

    # Check that coefficients are close to true values
    assert np.isclose(model.coefficients[0], 1.0, atol=0.1) # intercept
    assert np.isclose(model.coefficients[1], 2.0, atol=0.1) # slope

def test_ols_confidence_intervals():
    """Test that confidence intervals contain true coefficients."""
    np.random.seed(42)
    n = 200
    X = np.random.randn(n, 2)
    true_beta = np.array([1.0, 2.0, 3.0]) # intercept=1, slope1=2, slope2=3
    y = X @ true_beta[1:] + true_beta[0] + np.random.randn(n) * 0.1

    model = OLSModel()
    model.fit(X, y, confidence_level=0.95)

    # Check if true coefficients are within 95% CI
    # Note: This is probabilistic, but with high N and low noise, it should pass
    for i in range(3):
        ci = model.confidence_intervals[i]
        assert ci[0] <= true_beta[i] <= ci[1], f"True beta {i} ({true_beta[i]}) not in CI [{ci[0]}, {ci[1]}]"

def test_ols_r_squared():
    """Test R-squared calculation."""
    # Perfect fit
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([2, 4, 6, 8, 10])

    model = OLSModel()
    model.fit(X, y)

    assert np.isclose(model.r_squared, 1.0)

    # No relationship
    np.random.seed(42)
    X = np.random.randn(100, 1)
    y = np.random.randn(100)

    model = OLSModel()
    model.fit(X, y)

    assert 0 <= model.r_squared <= 1

def test_ols_rank_deficient():
    """Test handling of rank-deficient design matrix."""
    # Create collinear features
    X = np.array([[1, 1], [2, 2], [3, 3], [4, 4]])
    y = np.array([1, 2, 3, 4])

    model = OLSModel()
    with pytest.raises(ValueError, match="rank-deficient"):
        model.fit(X, y)

def test_fit_ols_and_get_intervals_function():
    """Test the convenience function."""
    np.random.seed(42)
    n = 50
    X = np.random.randn(n, 1)
    y = 3 * X.flatten() + 2 + np.random.randn(n) * 0.5

    results = fit_ols_and_get_intervals(X, y)

    assert "coefficients" in results
    assert "standard_errors" in results
    assert "confidence_intervals" in results
    assert "r_squared" in results
    assert len(results["coefficients"]) == 2 # intercept + 1 slope
    assert len(results["confidence_intervals"]) == 2