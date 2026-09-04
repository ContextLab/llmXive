import numpy as np
import pytest
import logging
from src.stats import calculate_vif, run_regression, run_cross_validation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestVIFCalculation:
    """Unit tests for VIF calculation."""

    def test_vif_no_correlation(self):
        """Test VIF on uncorrelated features (should be close to 1)."""
        np.random.seed(42)
        # Generate uncorrelated data
        X = np.random.randn(100, 3)
        vif_results = calculate_vif(X)
        
        for vif in vif_results.values():
            assert 0.9 < vif < 1.1, f"VIF should be ~1 for uncorrelated features, got {vif}"

    def test_vif_high_correlation(self):
        """Test VIF on highly correlated features (should be high)."""
        # Create features with high correlation
        X = np.random.randn(100, 2)
        X[:, 1] = X[:, 0] * 0.99 + np.random.randn(100) * 0.01  # Highly correlated
        
        vif_results = calculate_vif(X)
        
        for vif in vif_results.values():
            assert vif > 10, f"VIF should be high for correlated features, got {vif}"

    def test_vif_single_feature(self):
        """Test VIF with a single feature (should be 1)."""
        X = np.random.randn(50, 1)
        vif_results = calculate_vif(X)
        
        assert len(vif_results) == 1
        assert vif_results['feature_0'] == 1.0

class TestRidgeFallbackLogic:
    """Unit tests for Ridge regression fallback logic."""

    def test_ridge_fallback_on_high_vif(self):
        """Test that Ridge is used when VIF exceeds threshold."""
        # Create highly correlated data
        np.random.seed(42)
        X = np.random.randn(100, 2)
        X[:, 1] = X[:, 0] * 0.99 + np.random.randn(100) * 0.01
        y = X[:, 0] + X[:, 1] + np.random.randn(100) * 0.1
        
        result = run_regression(X, y, vif_threshold=5.0, ridge_alpha=0.5)
        
        assert result['model_type'] == 'Ridge', "Should switch to Ridge on high VIF"
        assert result['vif_check']['switched_to_ridge'] is True
        assert result['ridge_alpha_used'] == 0.5

    def test_linear_regression_on_low_vif(self):
        """Test that LinearRegression is used when VIF is low."""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = X[:, 0] + X[:, 1] + np.random.randn(100) * 0.1
        
        result = run_regression(X, y, vif_threshold=5.0)
        
        assert result['model_type'] == 'LinearRegression', "Should use LinearRegression on low VIF"
        assert result['vif_check']['switched_to_ridge'] is False

class TestRegressionOutput:
    """Unit tests for regression output structure and values."""

    def test_regression_output_structure(self):
        """Test that regression output contains all required fields."""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X[:, 0] + X[:, 1] + np.random.randn(50) * 0.1
        
        result = run_regression(X, y)
        
        required_fields = ['model_type', 'degree', 'r_squared', 'coefficients', 
                         'p_values', 'vif_check', 'n_samples', 'n_features']
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_polynomial_regression(self):
        """Test polynomial regression with degree > 1."""
        np.random.seed(42)
        X = np.random.randn(100, 1)
        y = X[:, 0]**2 + X[:, 0] + np.random.randn(100) * 0.1
        
        result = run_regression(X, y, degree=2)
        
        assert result['degree'] == 2
        assert result['model_type'] in ['LinearRegression', 'Ridge']
        # R² should be reasonably high for this synthetic data
        assert result['r_squared'] > 0.8

    def test_r_squared_bounds(self):
        """Test that R² is within expected bounds."""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = np.random.randn(50)
        
        result = run_regression(X, y)
        
        # R² can be negative for poor fits, but typically between -inf and 1
        assert result['r_squared'] <= 1.0

class TestCrossValidation:
    """Unit tests for cross-validation logic."""

    def test_cv_output_structure(self):
        """Test that CV output contains all required fields."""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = X[:, 0] + X[:, 1] + np.random.randn(100) * 0.1
        
        result = run_cross_validation(X, y, cv_folds=5)
        
        required_fields = ['model_type', 'degree', 'cv_folds', 'mean_score', 
                         'std_score', 'fold_scores', 'stability_flag']
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_cv_fold_count(self):
        """Test that the number of fold scores matches cv_folds."""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = X[:, 0] + X[:, 1] + np.random.randn(100) * 0.1
        
        for folds in [3, 5, 10]:
            result = run_cross_validation(X, y, cv_folds=folds)
            assert len(result['fold_scores']) == folds
            assert result['cv_folds'] == folds

    def test_cv_stability_flag(self):
        """Test stability flag based on std dev."""
        np.random.seed(42)
        # Create stable data
        X = np.random.randn(200, 2)
        y = X[:, 0] + X[:, 1] + np.random.randn(200) * 0.01
        
        result = run_cross_validation(X, y, cv_folds=5)
        
        if result['std_score'] <= 0.1:
            assert result['stability_flag'] == 'STABLE'
        else:
            assert result['stability_flag'] == 'UNSTABLE'

class TestSmallDatasetHandling:
    """Unit tests for small dataset handling."""

    def test_small_dataset_regression(self):
        """Test regression on a small dataset (N < 10)."""
        np.random.seed(42)
        X = np.random.randn(5, 2)
        y = X[:, 0] + X[:, 1] + np.random.randn(5) * 0.1
        
        # Should not raise an error, but may produce unreliable results
        result = run_regression(X, y)
        
        assert result['n_samples'] == 5
        assert 'r_squared' in result

    def test_very_small_dataset_cv(self):
        """Test cross-validation on a very small dataset."""
        np.random.seed(42)
        X = np.random.randn(8, 2)
        y = X[:, 0] + X[:, 1] + np.random.randn(8) * 0.1
        
        # With N=8 and 5 folds, each fold will have very few samples
        # This may raise warnings or errors depending on sklearn version
        # We expect it to run but with potentially unstable results
        result = run_cross_validation(X, y, cv_folds=3)  # Reduce folds for small N
        
        assert result['n_samples'] == 8
        assert 'mean_score' in result