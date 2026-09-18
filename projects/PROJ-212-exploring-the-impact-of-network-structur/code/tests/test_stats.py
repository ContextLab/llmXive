import numpy as np
import pytest
import logging
from unittest.mock import patch, MagicMock
from src.stats import calculate_vif, run_regression, run_cross_validation, calculate_anova_table
import warnings

class TestVIFCalculation:
    def test_vif_high_correlation(self):
        """Test VIF calculation with highly correlated features."""
        # Create a matrix with high correlation
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 0.95 + np.random.randn(n) * 0.1  # Highly correlated with x1
        X = np.column_stack([x1, x2])
        
        vif_values = calculate_vif(X)
        
        # Both features should have VIF > 5 due to high correlation
        assert len(vif_values) == 2
        # At least one should have high VIF
        high_vif_count = sum(1 for v in vif_values.values() if v > 5)
        assert high_vif_count >= 1, f"Expected at least one feature with VIF > 5, got: {vif_values}"

    def test_vif_low_correlation(self):
        """Test VIF calculation with uncorrelated features."""
        n = 100
        X = np.random.randn(n, 3)
        
        vif_values = calculate_vif(X)
        
        # All VIFs should be close to 1 for uncorrelated features
        for vif in vif_values.values():
            assert vif < 5, f"Expected VIF < 5 for uncorrelated features, got: {vif_values}"

class TestRegressionFunctions:
    def test_ridge_fallback_on_high_vif(self):
        """Test that the system switches to Ridge Regression when VIF > 5 and logs the alpha parameter."""
        # Create data with high correlation to trigger VIF > 5
        n = 50
        x1 = np.random.randn(n)
        x2 = x1 * 0.98 + np.random.randn(n) * 0.05  # Very high correlation
        X = np.column_stack([x1, x2])
        y = x1 + x2 + np.random.randn(n) * 0.1
        
        # Capture log output
        with patch('src.stats.logger') as mock_logger:
            result = run_regression(X, y, alpha=2.5)
            
            # Verify model type is Ridge
            assert result["model_type"] == "Ridge", f"Expected Ridge model, got {result['model_type']}"
            
            # Verify alpha parameter is documented
            assert result["alpha"] == 2.5, f"Expected alpha 2.5, got {result['alpha']}"
            
            # Verify warning was logged about VIF and alpha
            warning_calls = [call for call in mock_logger.warning.call_args_list if "High VIF" in str(call)]
            info_calls = [call for call in mock_logger.info.call_args_list if "alpha" in str(call).lower()]
            
            assert len(warning_calls) > 0, "Expected warning log about high VIF"
            assert len(info_calls) > 0 or any("alpha=2.5" in str(call) for call in warning_calls), \
                "Expected log entry documenting the alpha parameter used"

    def test_linear_regression_no_high_vif(self):
        """Test that Linear Regression is used when VIF <= 5."""
        n = 50
        X = np.random.randn(n, 3)
        y = X[:, 0] + X[:, 1] * 2 + np.random.randn(n) * 0.1
        
        result = run_regression(X, y, alpha=1.0)
        
        assert result["model_type"] == "Linear"
        assert result["alpha"] == 0.0

    def test_force_ridge_regression(self):
        """Test that Ridge regression is used when force flag is set."""
        n = 50
        X = np.random.randn(n, 3)
        y = X[:, 0] + np.random.randn(n) * 0.1
        
        result = run_regression(X, y, use_ridge=True, alpha=0.5)
        
        assert result["model_type"] == "Ridge"
        assert result["alpha"] == 0.5

class TestCrossValidation:
    def test_cv_basic(self):
        """Test basic cross-validation functionality."""
        n = 100
        X = np.random.randn(n, 3)
        y = X[:, 0] + X[:, 1] * 2 + np.random.randn(n) * 0.1
        
        cv_result = run_cross_validation(X, y, n_folds=5)
        
        assert "mean_r2" in cv_result
        assert "std_r2" in cv_result
        assert isinstance(cv_result["mean_r2"], float)
        assert isinstance(cv_result["std_r2"], float)
        assert cv_result["mean_r2"] <= 1.0
        assert cv_result["std_r2"] >= 0.0

class TestFeatureAuthorization:
    def test_filter_authorized_features(self):
        """Test that only authorized features are kept."""
        from src.stats import filter_authorized_features
        
        features = {
            "degree": 5.0,
            "clustering": 0.3,
            "path_length": 10.0,
            "unauthorized_feature": 99.0
        }
        
        filtered = filter_authorized_features(features)
        
        assert "degree" in filtered
        assert "clustering" in filtered
        assert "path_length" in filtered
        assert "unauthorized_feature" not in filtered

class TestRegressionDataPreparation:
    def test_prepare_regression_data(self):
        """Test data preparation for regression."""
        from src.stats import prepare_regression_data
        
        data = [
            {"degree": 5.0, "clustering": 0.3, "path_length": 10.0, "threshold": 2.5},
            {"degree": 3.0, "clustering": 0.5, "path_length": 8.0, "threshold": 1.8},
            {"degree": 7.0, "clustering": 0.2, "path_length": 12.0, "threshold": 3.1}
        ]
        
        X, y, features = prepare_regression_data(data)
        
        assert X.shape[0] == 3
        assert X.shape[1] == 3
        assert len(y) == 3
        assert features == ["degree", "clustering", "path_length"]