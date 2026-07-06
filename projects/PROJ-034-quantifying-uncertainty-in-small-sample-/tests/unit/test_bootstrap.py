"""
Unit tests for the bootstrap model implementation.
"""
import numpy as np
import pytest
from models.bootstrap import BootstrapModel, fit_bootstrap_and_get_intervals

@pytest.fixture
def simple_data():
    """Create a simple linear dataset for testing."""
    np.random.seed(42)
    n = 50
    X = np.random.randn(n, 2)
    true_beta = np.array([1.5, -2.0])
    y = X @ true_beta + np.random.randn(n) * 0.5
    return X, y, true_beta

def test_bootstrap_model_fit(simple_data):
    """Test that the bootstrap model can fit and return coefficients."""
    X, y, _ = simple_data
    model = BootstrapModel(n_bootstraps=100, random_state=42)
    model.fit(X, y)
    
    assert model.coefficients_ is not None
    assert len(model.coefficients_) == 2
    assert isinstance(model.intervals_, dict)
    assert "beta_0" in model.intervals_
    assert "beta_1" in model.intervals_

def test_bootstrap_intervals_valid(simple_data):
    """Test that bootstrap intervals are valid (lower < upper)."""
    X, y, _ = simple_data
    model = BootstrapModel(n_bootstraps=200, random_state=42)
    model.fit(X, y)
    
    for coef_name, (lower, upper) in model.intervals_.items():
        assert lower < upper, f"Invalid interval for {coef_name}: {lower} >= {upper}"

def test_fit_bootstrap_and_get_intervals(simple_data):
    """Test the convenience function."""
    X, y, true_beta = simple_data
    coeffs, intervals = fit_bootstrap_and_get_intervals(
        X, y, 
        n_bootstraps=100, 
        random_state=42
    )
    
    assert coeffs.shape == (2,)
    assert isinstance(intervals, dict)
    assert len(intervals) == 2

def test_bootstrap_with_small_sample():
    """Test bootstrap with a very small sample (edge case)."""
    np.random.seed(123)
    n = 10
    X = np.random.randn(n, 1)
    y = X * 2.0 + np.random.randn(n) * 0.1
    
    model = BootstrapModel(n_bootstraps=50, random_state=42)
    model.fit(X, y)
    
    assert model.coefficients_ is not None
    assert len(model.intervals_) == 1

def test_reproducibility(simple_data):
    """Test that results are reproducible with same seed."""
    X, y, _ = simple_data
    
    model1 = BootstrapModel(n_bootstraps=100, random_state=99)
    model1.fit(X, y)
    
    model2 = BootstrapModel(n_bootstraps=100, random_state=99)
    model2.fit(X, y)
    
    np.testing.assert_array_almost_equal(
        model1.coefficients_, 
        model2.coefficients_
    )
    assert model1.intervals_ == model2.intervals_

def test_confidence_level_impact(simple_data):
    """Test that different confidence levels produce different intervals."""
    X, y, _ = simple_data
    
    model_90 = BootstrapModel(n_bootstraps=200, confidence_level=0.90, random_state=42)
    model_90.fit(X, y)
    
    model_99 = BootstrapModel(n_bootstraps=200, confidence_level=0.99, random_state=42)
    model_99.fit(X, y)
    
    # 99% intervals should be wider than 90% intervals
    for coef_name in model_90.intervals_:
        width_90 = model_90.intervals_[coef_name][1] - model_90.intervals_[coef_name][0]
        width_99 = model_99.intervals_[coef_name][1] - model_99.intervals_[coef_name][0]
        assert width_99 >= width_90, f"99% interval should be wider than 90% for {coef_name}"
