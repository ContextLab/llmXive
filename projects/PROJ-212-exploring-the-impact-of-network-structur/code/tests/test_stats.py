import numpy as np
import pytest
import logging
from src.stats import calculate_vif, run_regression, run_cross_validation

logger = logging.getLogger(__name__)

class TestVIFCalculation:
    def test_vif_perfect_collinearity(self):
        """Test VIF when one feature is a perfect linear combination of another."""
        # X[:, 1] = 2 * X[:, 0]
        X = np.array([
            [1, 2],
            [2, 4],
            [3, 6],
            [4, 8],
            [5, 10],
            [6, 12],
            [7, 14],
            [8, 16],
            [9, 18],
            [10, 20]
        ])
        vif = calculate_vif(X)
        # One of the VIFs should be very large (or inf)
        assert any(v == np.inf or v > 1000 for v in vif.values()), "VIF should be high for collinear features"

    def test_vif_independent_features(self):
        """Test VIF with uncorrelated random features."""
        np.random.seed(42)
        X = np.random.rand(100, 3)
        vif = calculate_vif(X)
        # VIF should be close to 1 for independent features
        for v in vif.values():
            assert 0.9 <= v <= 1.5, f"VIF {v} is unexpectedly high for independent features"

class TestRidgeFallbackLogic:
    def test_ridge_fallback_on_high_vif(self):
        """Test that run_regression switches to Ridge when VIF > threshold."""
        # Create data with high multicollinearity
        X = np.array([
            [1, 2],
            [2, 4],
            [3, 6],
            [4, 8],
            [5, 10],
            [6, 12],
            [7, 14],
            [8, 16],
            [9, 18],
            [10, 20],
            [11, 22],
            [12, 24]
        ])
        y = np.array([3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36])
        
        result = run_regression(X, y, vif_threshold=5.0)
        assert result["model_type"] == "Ridge", "Should fallback to Ridge for high VIF"
        assert "High multicollinearity detected" in str(result["warnings"])

    def test_linear_regression_on_low_vif(self):
        """Test that run_regression uses LinearRegression when VIF is low."""
        np.random.seed(42)
        X = np.random.rand(50, 2)
        y = np.sum(X, axis=1) + np.random.normal(0, 0.1, 50)
        
        result = run_regression(X, y, vif_threshold=5.0)
        assert result["model_type"] == "Linear", "Should use LinearRegression for low VIF"

class TestRegressionOutput:
    def test_regression_output_structure(self):
        """Test that run_regression returns the expected keys."""
        np.random.seed(42)
        X = np.random.rand(50, 2)
        y = np.sum(X, axis=1)
        
        result = run_regression(X, y)
        
        required_keys = ["model_type", "coefficients", "intercept", "r_squared", "p_values", "warnings"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_regression_small_dataset_warning(self):
        """Test that a warning is generated for small datasets (N < 10)."""
        # Create a dataset with N < 10
        X = np.array([
            [1, 2],
            [3, 4],
            [5, 6],
            [7, 8],
            [9, 10]
        ])
        y = np.array([3, 7, 11, 15, 19])
        
        result = run_regression(X, y)
        assert "Small dataset detected" in str(result["warnings"]), "Should warn about small dataset"

class TestCrossValidation:
    def test_cv_output_structure(self):
        """Test that run_cross_validation returns the expected keys."""
        np.random.seed(42)
        X = np.random.rand(100, 2)
        y = np.sum(X, axis=1)
        
        result = run_cross_validation(X, y)
        
        required_keys = ["mean_r2", "std_r2", "stability_flag", "scores"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_cv_stability_flag(self):
        """Test that stability_flag is True when std dev <= 0.1."""
        np.random.seed(42)
        # Create a very stable relationship
        X = np.random.rand(200, 2)
        y = X[:, 0] + X[:, 1] + np.random.normal(0, 0.01, 200)
        
        result = run_cross_validation(X, y)
        # With such low noise, stability should be true
        assert result["stability_flag"] == True, "Stability flag should be True for stable data"

    def test_cv_insufficient_samples(self):
        """Test CV behavior when samples < n_splits."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([3, 7, 11])
        
        result = run_cross_validation(X, y, n_splits=5)
        assert result["mean_r2"] is None, "Mean R2 should be None for insufficient samples"
        assert "Insufficient samples" in result["message"]

class TestSmallDatasetHandling:
    """Specific tests for T019: handling of small datasets (<10) with warning generation."""
    
    def test_warning_generated_for_n_less_than_10(self):
        """Verify that a descriptive warning is generated when N < 10."""
        # Create a dataset with exactly 9 samples
        X = np.random.rand(9, 2)
        y = np.random.rand(9)
        
        result = run_regression(X, y)
        
        # Check that a warning exists and mentions the small dataset
        assert len(result["warnings"]) > 0, "Warnings list should not be empty"
        warning_found = any("Small dataset" in w for w in result["warnings"])
        assert warning_found, f"Expected 'Small dataset' warning, got: {result['warnings']}"
        
        # Verify the warning mentions the count
        assert "N=9" in str(result["warnings"]), "Warning should specify the sample size"
    
    def test_no_warning_for_n_greater_equal_10(self):
        """Verify that no small dataset warning is generated when N >= 10."""
        # Create a dataset with exactly 10 samples
        X = np.random.rand(10, 2)
        y = np.random.rand(10)
        
        result = run_regression(X, y)
        
        # Check that no small dataset warning exists
        warning_found = any("Small dataset" in w for w in result["warnings"])
        assert not warning_found, f"Unexpected small dataset warning for N=10: {result['warnings']}"
    
    def test_regression_runs_on_small_dataset(self):
        """Verify that regression still runs and returns results even for N < 10."""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y = np.array([3, 7, 11, 15, 19])
        
        result = run_regression(X, y)
        
        assert result["model_type"] in ["Linear", "Ridge"], "Model type should be set"
        assert "r_squared" in result, "R-squared should be calculated"
        assert result["n_samples"] == 5, "Sample count should be recorded"