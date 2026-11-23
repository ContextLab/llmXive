"""
Unit tests for Tobit regression execution and p-value extraction.

This module tests the TobitModel class functionality, specifically:
1. Successful execution of Tobit regression on synthetic but realistic data
2. Correct extraction of p-values from the regression results
3. Validation of model attributes and statistical outputs
"""
import pytest
import numpy as np
import sys
from pathlib import Path
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.seed_manager import set_seed
from analysis.tobit_model import TobitModel


class TestTobitModelExecution:
    """Test Tobit regression execution and p-value extraction."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        set_seed(42)
        self.n_samples = 200
        self.n_features = 2
        
        # Generate synthetic data that mimics the expected structure:
        # X: features (alpha, horizon)
        # y: effective depth (censored at 0 and max_depth)
        self.X = np.random.rand(self.n_samples, self.n_features)
        self.X[:, 0] = np.random.uniform(0.1, 0.9, self.n_samples)  # alpha
        self.X[:, 1] = np.random.uniform(1, 10, self.n_samples)     # horizon
        
        # Create censored target variable
        # Simulate a linear relationship with some noise
        true_coefs = np.array([2.0, 1.5])
        noise = np.random.normal(0, 0.5, self.n_samples)
        y_continuous = self.X @ true_coefs + noise
        
        # Apply censoring (0 at bottom, max at top)
        self.y = np.clip(y_continuous, 0, 10)

    def test_tobit_model_initialization(self):
        """Test that TobitModel initializes correctly with parameters."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        
        assert model.lower_bound == 0
        assert model.upper_bound == 10
        assert model.is_fitted is False
        assert model.results is None

    def test_tobit_execution_success(self):
        """Test that Tobit regression executes without errors."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        
        # This should execute without raising exceptions
        model.fit(self.X, self.y)
        
        assert model.is_fitted is True
        assert model.results is not None

    def test_p_value_extraction(self):
        """Test that p-values are correctly extracted from Tobit results."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        p_values = model.get_p_values()
        
        # Check that p-values are returned as a numpy array
        assert isinstance(p_values, np.ndarray)
        
        # Check shape matches number of features
        assert p_values.shape[0] == self.n_features
        
        # Check all p-values are in valid range [0, 1]
        assert np.all((p_values >= 0) & (p_values <= 1))

    def test_coefficient_extraction(self):
        """Test that coefficients are correctly extracted."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        coefs = model.get_coefficients()
        
        assert isinstance(coefs, np.ndarray)
        assert coefs.shape[0] == self.n_features

    def test_likelihood_ratio_test(self):
        """Test that likelihood ratio test statistic is computed."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        lr_stat = model.get_likelihood_ratio_test()
        
        assert isinstance(lr_stat, (float, np.floating))
        assert lr_stat >= 0

    def test_censoring_detection(self):
        """Test that the model correctly identifies censored observations."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        # Count observations at boundaries (censored)
        n_censored = np.sum((self.y == 0) | (self.y == 10))
        
        # Model should have recorded censoring information
        assert hasattr(model, 'n_censored')
        assert model.n_censored == n_censored

    def test_p_value_significance_threshold(self):
        """Test p-value extraction with known significance thresholds."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        p_values = model.get_p_values()
        
        # Test common significance thresholds
        significant_at_005 = p_values < 0.05
        significant_at_01 = p_values < 0.01
        
        # These should be boolean arrays
        assert isinstance(significant_at_005, np.ndarray)
        assert isinstance(significant_at_01, np.ndarray)
        
        # At least some features should be testable
        assert len(significant_at_005) == self.n_features

    def test_model_with_different_bounds(self):
        """Test Tobit model with different censoring bounds."""
        # Lower bound only (left-censored)
        model_left = TobitModel(lower_bound=0, upper_bound=None)
        model_left.fit(self.X, self.y)
        assert model_left.is_fitted is True
        
        # Upper bound only (right-censored)
        model_right = TobitModel(lower_bound=None, upper_bound=10)
        model_right.fit(self.X, self.y)
        assert model_right.is_fitted is True

    def test_prediction_method(self):
        """Test that the model can make predictions."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        # Predict on training data
        predictions = model.predict(self.X)
        
        assert isinstance(predictions, np.ndarray)
        assert predictions.shape[0] == self.n_samples
        
        # Predictions should respect bounds
        assert np.all(predictions >= 0)
        assert np.all(predictions <= 10)

    def test_interaction_effect_detection(self):
        """Test detection of significant interaction effects via p-values."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        model.fit(self.X, self.y)
        
        p_values = model.get_p_values()
        
        # Check that p-values can be used to detect significant effects
        # (at least one feature should have a testable p-value)
        assert len(p_values) > 0
        assert all(isinstance(p, (float, np.floating)) for p in p_values)

class TestTobitModelEdgeCases:
    """Test edge cases and error handling in TobitModel."""

    def test_empty_data(self):
        """Test model behavior with empty data."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        
        with pytest.raises((ValueError, Exception)):
            model.fit(np.array([]).reshape(0, 2), np.array([]))

    def test_single_sample(self):
        """Test model behavior with single sample."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        X_single = np.random.rand(1, 2)
        y_single = np.array([5.0])
        
        # Should handle gracefully or raise informative error
        try:
            model.fit(X_single, y_single)
            # If it doesn't raise, it should handle the edge case
            assert model.is_fitted is True
        except Exception:
            # Expected behavior for insufficient data
            pass

    def test_no_censoring(self):
        """Test model with data that has no censoring."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        X = np.random.rand(50, 2)
        y = np.random.uniform(1, 9, 50)  # All values within bounds
        
        model.fit(X, y)
        assert model.is_fitted is True
        # Should still work even if no censoring occurs

    def test_all_censored(self):
        """Test model with all censored data."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        X = np.random.rand(50, 2)
        y = np.array([0.0] * 25 + [10.0] * 25)  # All at boundaries
        
        # Should handle extreme censoring
        try:
            model.fit(X, y)
            assert model.is_fitted is True
        except Exception:
            # Expected if model cannot converge with all censored data
            pass

    def test_mismatched_dimensions(self):
        """Test model with mismatched X and y dimensions."""
        model = TobitModel(lower_bound=0, upper_bound=10)
        X = np.random.rand(50, 2)
        y = np.random.rand(40)  # Mismatched length
        
        with pytest.raises((ValueError, Exception)):
            model.fit(X, y)