import numpy as np
import pytest
import logging
from unittest.mock import patch, MagicMock
from src.stats import calculate_vif, run_regression, run_cross_validation, calculate_anova_table

logger = logging.getLogger(__name__)

class TestRegressionFitting:
    def test_linear_regression_basic(self):
        """Test basic linear regression fitting"""
        np.random.seed(42)
        X = np.random.rand(100, 1)
        y = 2 * X.squeeze() + 1 + np.random.normal(0, 0.1, 100)
        
        result = run_regression(X, y, degree=1)
        
        assert "coefficients" in result
        assert "intercept" in result
        assert "r_squared" in result
        assert "p_values" in result
        assert "anova" in result
        
        # R² should be high for this synthetic data
        assert result["r_squared"] > 0.8
        
        # Coefficient should be close to 2
        assert abs(result["coefficients"][0] - 2.0) < 0.2

    def test_polynomial_regression(self):
        """Test polynomial regression fitting"""
        np.random.seed(42)
        X = np.linspace(-1, 1, 100).reshape(-1, 1)
        y = X.squeeze()**2 + 0.5 * X.squeeze() + np.random.normal(0, 0.05, 100)
        
        result = run_regression(X, y, degree=2)
        
        assert result["model_type"] == "polynomial"
        assert result["degree"] == 2
        assert result["r_squared"] > 0.9

    def test_small_sample_size(self):
        """Test regression with very small sample size"""
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])
        
        # Should handle small sample without crashing
        result = run_regression(X, y, degree=1)
        
        assert "coefficients" in result
        # P-values might be NaN due to insufficient degrees of freedom
        assert len(result["p_values"]) == 1

    def test_high_dimensional_data(self):
        """Test regression with more features than samples"""
        X = np.random.rand(5, 10)  # 5 samples, 10 features
        y = np.random.rand(5)
        
        # Should handle gracefully
        result = run_regression(X, y, degree=1)
        
        assert "coefficients" in result
        # R² might be 1.0 or close due to overfitting
        assert result["r_squared"] >= 0.0

class TestVIFCalculation:
    def test_vif_no_multicollinearity(self):
        """Test VIF with uncorrelated features"""
        np.random.seed(42)
        X = np.random.rand(100, 3)
        
        vif_values = calculate_vif(X)
        
        # VIF should be close to 1 for uncorrelated features
        for name, vif in vif_values.items():
            assert 1.0 <= vif < 5.0, f"VIF for {name} should be < 5, got {vif}"

    def test_vif_high_multicollinearity(self):
        """Test VIF with highly correlated features"""
        np.random.seed(42)
        X = np.random.rand(100, 2)
        # Create high correlation
        X[:, 1] = X[:, 0] + np.random.normal(0, 0.01, 100)
        
        vif_values = calculate_vif(X)
        
        # At least one VIF should be high (> 5)
        high_vif_found = any(vif > 5 for vif in vif_values.values())
        assert high_vif_found, "Expected high VIF for correlated features"

    def test_vif_feature_names(self):
        """Test VIF with custom feature names"""
        X = np.random.rand(50, 2)
        names = ["feature_a", "feature_b"]
        
        vif_values = calculate_vif(X, feature_names=names)
        
        assert set(vif_values.keys()) == set(names)

    def test_vif_small_sample(self):
        """Test VIF with too few samples"""
        X = np.random.rand(2, 5)  # Only 2 samples for 5 features
        
        vif_values = calculate_vif(X)
        
        # Should return NaN or handle gracefully
        for vif in vif_values.values():
            assert np.isnan(vif) or vif > 0

class TestCrossValidation:
    def test_cross_validation_basic(self):
        """Test basic cross-validation execution"""
        np.random.seed(42)
        X = np.random.rand(200, 2)
        y = X[:, 0] + X[:, 1] + np.random.normal(0, 0.1, 200)
        
        result = run_cross_validation(X, y, n_splits=5, cv_repeats=5)
        
        assert "mean_r2" in result
        assert "std_r2" in result
        assert "all_scores" in result
        assert result["n_folds"] == 5
        assert result["n_repeats"] == 5
        assert len(result["all_scores"]) == 25  # 5 * 5

    def test_cross_validation_stability(self):
        """Test cross-validation stability flagging"""
        np.random.seed(42)
        X = np.random.rand(500, 2)
        y = X[:, 0] + np.random.normal(0, 0.01, 500)  # Very predictable
        
        result = run_cross_validation(X, y)
        
        # Should be stable (low std dev)
        assert result["stability_flag"] == False

    def test_cross_validation_unstable(self):
        """Test cross-validation with unstable model"""
        np.random.seed(42)
        X = np.random.rand(100, 5)
        y = np.random.rand(100)  # Random target, no pattern
        
        result = run_cross_validation(X, y)
        
        # Might be unstable, but at least should run
        assert "mean_r2" in result
        assert "std_r2" in result

    def test_polynomial_cross_validation(self):
        """Test cross-validation with polynomial features"""
        np.random.seed(42)
        X = np.linspace(-1, 1, 200).reshape(-1, 1)
        y = X.squeeze()**2 + np.random.normal(0, 0.05, 200)
        
        result = run_cross_validation(X, y, degree=2)
        
        assert result["mean_r2"] > 0.8

class TestSmallDatasetHandling:
    def test_regression_warning_small_n(self):
        """Test that regression handles small N gracefully"""
        X = np.array([[1], [2], [3], [4]])
        y = np.array([1, 2, 3, 4])
        
        result = run_regression(X, y)
        
        assert result["r_squared"] >= 0.0

    def test_vif_insufficient_data(self):
        """Test VIF with insufficient data"""
        X = np.random.rand(3, 5)
        
        vif_values = calculate_vif(X)
        
        # Should return NaN for all
        assert all(np.isnan(vif) for vif in vif_values.values())

    def test_cv_small_dataset(self):
        """Test cross-validation with very small dataset"""
        X = np.random.rand(10, 2)
        y = np.random.rand(10)
        
        result = run_cross_validation(X, y, n_splits=3, cv_repeats=2)
        
        # Should run without crashing
        assert "mean_r2" in result
        assert len(result["all_scores"]) == 6

class TestANOVA:
    def test_anova_basic(self):
        """Test ANOVA table calculation"""
        y = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        
        anova = calculate_anova_table(y, y_pred)
        
        assert "source" in anova
        assert "df" in anova
        assert "ss" in anova
        assert len(anova["source"]) == 3
        assert anova["source"] == ["Regression", "Residual", "Total"]

    def test_anova_sum_squares(self):
        """Test that sum of squares add up correctly"""
        y = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        
        anova = calculate_anova_table(y, y_pred)
        
        ss_total = anova["ss"][2]
        ss_regression = anova["ss"][0]
        ss_residual = anova["ss"][1]
        
        # SS_total should equal SS_regression + SS_residual
        assert np.isclose(ss_total, ss_regression + ss_residual)