"""
Unit tests for Gaussian Process Regressor implementation.
"""
import pytest
import numpy as np
import warnings
from sklearn.exceptions import ConvergenceWarning

from code.models.gpr import GaussianProcessUQ, train_gpr, run_gpr_inference


@pytest.fixture
def dummy_data():
    """Generate simple dummy data for testing."""
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.sum(X, axis=1) + np.random.normal(0, 0.1, 100)
    return X, y


def test_gpr_initialization():
    """Test that GPR model initializes correctly."""
    model = GaussianProcessUQ()
    assert model.length_scale == 1.0
    assert model.noise_level == 0.1
    assert model.random_state == 42
    assert not model.is_fitted


def test_gpr_fit(dummy_data):
    """Test that GPR model fits without error."""
    X, y = dummy_data
    model = GaussianProcessUQ()
    
    # Should not raise
    model.fit(X, y)
    
    assert model.is_fitted


def test_gpr_predict(dummy_data):
    """Test that GPR model predicts correctly."""
    X, y = dummy_data
    model = GaussianProcessUQ()
    model.fit(X, y)
    
    mean, std = model.predict(X)
    
    assert mean.shape == (100,)
    assert std.shape == (100,)
    assert np.all(std >= 0)


def test_gpr_predict_interval(dummy_data):
    """Test that GPR model returns valid intervals."""
    X, y = dummy_data
    model = GaussianProcessUQ()
    model.fit(X, y)
    
    mean, lower, upper = model.predict_interval(X, confidence_level=0.95)
    
    assert mean.shape == (100,)
    assert lower.shape == (100,)
    assert upper.shape == (100,)
    assert np.all(lower <= mean)
    assert np.all(mean <= upper)


def test_gpr_predict_unfitted():
    """Test that prediction fails on unfitted model."""
    model = GaussianProcessUQ()
    X = np.random.rand(10, 5)
    
    with pytest.raises(RuntimeError, match="Model must be fitted"):
        model.predict(X)


def test_train_gpr_helper(dummy_data):
    """Test the train_gpr helper function."""
    X, y = dummy_data
    model = train_gpr(X, y)
    
    assert model.is_fitted
    
    results = run_gpr_inference(model, X)
    assert "mean" in results
    assert "lower_bound" in results
    assert "upper_bound" in results
    assert "std" in results


def test_gpr_with_custom_params(dummy_data):
    """Test GPR with custom hyperparameters."""
    X, y = dummy_data
    model = GaussianProcessUQ(length_scale=2.0, noise_level=0.5, random_state=123)
    model.fit(X, y)
    
    assert model.length_scale == 2.0
    assert model.noise_level == 0.5
    assert model.random_state == 123


def test_gpr_convergence_handling(dummy_data):
    """Test that GPR handles convergence warnings gracefully."""
    X, y = dummy_data
    
    # Force a scenario that might trigger warnings (though unlikely with good data)
    # We just verify the code path exists and doesn't crash
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model = GaussianProcessUQ()
        model.fit(X, y)
        
        # The model should still be fitted even if warnings occurred
        assert model.is_fitted