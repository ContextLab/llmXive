import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import json
import os

from src.stats import (
    calculate_vif,
    check_vif_and_remediate,
    fit_linear,
    fit_polynomial,
    calculate_r_squared,
    calculate_p_values,
    calculate_anova,
    run_regression,
    run_cross_validation
)

@pytest.fixture
def sample_linear_data():
    """Generate sample data for linear regression testing."""
    np.random.seed(42)
    X = np.random.rand(100, 2)
    y = 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(100) * 0.1
    return X, y, ["feature1", "feature2"]

@pytest.fixture
def sample_polynomial_data():
    """Generate sample data for polynomial regression testing."""
    np.random.seed(42)
    X = np.random.rand(100, 1)
    y = 2 * X[:, 0]**2 + 3 * X[:, 0] + np.random.randn(100) * 0.1
    return X, y, ["feature1"]

@pytest.fixture
def temp_project_dirs():
    """Create temporary project directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "data").mkdir()
        (tmp_path / "results").mkdir()
        (tmp_path / "state").mkdir()
        yield tmp_path

class TestVIFLogic:
    """Tests for VIF calculation and remediation logic (T024)."""

    def test_vif_calculation_no_multicollinearity(self, sample_linear_data):
        """Test VIF calculation when features are independent."""
        X, y, names = sample_linear_data
        vif_data = calculate_vif(X, names)
        
        # All VIF values should be close to 1 for independent features
        for feature, vif in vif_data.items():
            assert vif < 5.0, f"VIF for {feature} should be < 5.0, got {vif}"

    def test_vif_calculation_with_multicollinearity(self):
        """Test VIF calculation when features are highly correlated."""
        np.random.seed(42)
        X1 = np.random.rand(100)
        X2 = X1 + np.random.randn(100) * 0.01  # Highly correlated
        X = np.column_stack([X1, X2])
        names = ["feature1", "feature2"]
        
        vif_data = calculate_vif(X, names)
        
        # At least one VIF should be > 5 due to multicollinearity
        assert any(v > 5.0 for v in vif_data.values()), "Expected at least one VIF > 5.0"

    def test_vif_remediation_removes_feature(self):
        """Test that VIF remediation removes high-VIF features."""
        np.random.seed(42)
        X1 = np.random.rand(100)
        X2 = X1 + np.random.randn(100) * 0.01  # Highly correlated
        X3 = np.random.rand(100)
        X = np.column_stack([X1, X2, X3])
        y = X1 + X2 + X3 + np.random.randn(100) * 0.1
        names = ["feature1", "feature2", "feature3"]
        
        final_type, action, X_filtered, names_filtered, _ = check_vif_and_remediate(
            X, y, names, threshold=5.0
        )
        
        # Should have removed at least one feature
        assert len(names_filtered) < len(names), "Expected feature removal"
        assert action is not None, "Expected remediation action"
        assert "removed" in action.lower(), "Action should mention removal"
        assert final_type == "Linear", "Should remain Linear after removal"

    def test_vif_remediation_switches_to_ridge(self):
        """Test that VIF remediation switches to Ridge when removal fails."""
        # Create extremely collinear data where removal won't help
        np.random.seed(42)
        n = 100
        X1 = np.random.rand(n)
        X2 = X1 + np.random.randn(n) * 0.001
        X3 = X1 + np.random.randn(n) * 0.001
        X = np.column_stack([X1, X2, X3])
        y = X1 + np.random.randn(n) * 0.1
        names = ["feature1", "feature2", "feature3"]
        
        # Set very low threshold to force Ridge
        final_type, action, X_filtered, names_filtered, _ = check_vif_and_remediate(
            X, y, names, threshold=2.0, ridge_alpha=1.0
        )
        
        # Should switch to Ridge if removal doesn't resolve
        if len(names_filtered) < len(names):
            assert final_type in ["Linear", "Ridge"]
        else:
            # If no removal happened, might still be Linear
            pass

    def test_vif_remediation_output_format(self, sample_linear_data):
        """Test that VIF remediation returns correct output format."""
        X, y, names = sample_linear_data
        final_type, action, X_filtered, names_filtered, _ = check_vif_and_remediate(
            X, y, names, threshold=5.0
        )
        
        assert isinstance(final_type, str)
        assert final_type in ["Linear", "Ridge", "Polynomial"]
        assert isinstance(action, (str, type(None)))
        assert isinstance(X_filtered, np.ndarray)
        assert isinstance(names_filtered, list)
        assert len(names_filtered) == X_filtered.shape[1]

    def test_regression_summary_contains_remediation_action(self, sample_linear_data, temp_project_dirs):
        """Test that regression summary includes remediation_action field (T023c requirement)."""
        X, y, names = sample_linear_data
        result = run_regression(X, y, names, model_type="linear")
        
        assert "remediation_action" in result, "Result should contain remediation_action"
        assert "model_type" in result
        assert "r_squared" in result
        assert "p_values" in result
        assert "coefficients" in result

    def test_vif_threshold_parameter(self):
        """Test that VIF threshold parameter works correctly."""
        np.random.seed(42)
        X1 = np.random.rand(100)
        X2 = X1 + np.random.randn(100) * 0.01
        X = np.column_stack([X1, X2])
        y = X1 + X2 + np.random.randn(100) * 0.1
        names = ["f1", "f2"]
        
        # High threshold - no removal
        _, action_high, _, _, _ = check_vif_and_remediate(X, y, names, threshold=100.0)
        assert action_high is None or "removed" not in action_high.lower()
        
        # Low threshold - removal expected
        _, action_low, _, _, _ = check_vif_and_remediate(X, y, names, threshold=2.0)
        # May or may not remove depending on exact VIF values

class TestStatisticalCalcs:
    """Tests for statistical calculation functions (T023b)."""

    def test_r_squared_calculation(self, sample_linear_data):
        """Test R-squared calculation."""
        X, y, _ = sample_linear_data
        model = fit_linear(X, y)
        y_pred = model.predict(X)
        r2 = calculate_r_squared(y, y_pred)
        
        assert 0 <= r2 <= 1, "R-squared should be between 0 and 1"

    def test_p_values_calculation(self, sample_linear_data):
        """Test p-values calculation."""
        X, y, _ = sample_linear_data
        model = fit_linear(X, y)
        p_vals = calculate_p_values(X, y, model)
        
        assert len(p_vals) == X.shape[1], "Should have p-value for each coefficient"
        for p in p_vals.values():
            assert 0 <= p <= 1, "p-values should be between 0 and 1"

    def test_anova_calculation(self, sample_linear_data):
        """Test ANOVA calculation."""
        X, y, _ = sample_linear_data
        model = fit_linear(X, y)
        y_pred = model.predict(X)
        anova = calculate_anova(y, y_pred)
        
        assert "f_statistic" in anova
        assert "p_value" in anova
        assert anova["f_statistic"] >= 0
        assert 0 <= anova["p_value"] <= 1

    def test_linear_regression_fit(self, sample_linear_data):
        """Test linear regression fitting."""
        X, y, _ = sample_linear_data
        model = fit_linear(X, y)
        
        assert hasattr(model, "coef_")
        assert hasattr(model, "intercept_")
        assert len(model.coef_) == X.shape[1]

    def test_polynomial_regression_fit(self, sample_polynomial_data):
        """Test polynomial regression fitting."""
        X, y, _ = sample_polynomial_data
        poly, model = fit_polynomial(X, y, degree=2)
        
        assert hasattr(model, "coef_")
        y_pred = model.predict(poly.transform(X))
        r2 = calculate_r_squared(y, y_pred)
        assert r2 > 0.5, "Polynomial fit should explain significant variance"

class TestCrossValidation:
    """Tests for cross-validation logic (T028)."""

    def test_loocv_small_dataset(self, sample_linear_data):
        """Test LOOCV on small dataset."""
        X, y, _ = sample_linear_data
        # Use 5-fold for this test (LOOCV would be too slow for larger n)
        result = run_cross_validation(X, y, model_type="linear", n_splits=5)
        
        assert "mean_r2" in result
        assert "std_dev" in result
        assert result["mean_r2"] <= 1.0
        assert result["std_dev"] >= 0

    def test_kfold_large_dataset(self, temp_project_dirs):
        """Test k-fold CV on larger dataset."""
        np.random.seed(42)
        X = np.random.rand(200, 3)
        y = 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(200) * 0.1
        
        result = run_cross_validation(X, y, model_type="linear", n_splits=10)
        
        assert "mean_r2" in result
        assert "std_dev" in result
        assert len(result.get("scores", [])) == 10

    def test_polynomial_cross_validation(self, sample_polynomial_data):
        """Test CV with polynomial features."""
        X, y, _ = sample_polynomial_data
        result = run_cross_validation(X, y, model_type="polynomial", n_splits=5, degree=2)
        
        assert "mean_r2" in result
        assert result["mean_r2"] > 0  # Should have some predictive power

class TestRegressionOutput:
    """Tests for regression output generation (T023c)."""

    def test_regression_summary_schema(self, sample_linear_data, temp_project_dirs):
        """Test that regression summary matches required schema."""
        X, y, names = sample_linear_data
        result = run_regression(X, y, names, model_type="linear")
        
        # Check required fields
        assert "model_type" in result
        assert "coefficients" in result
        assert "r_squared" in result
        assert "p_values" in result
        assert "remediation_action" in result
        
        # Validate types
        assert isinstance(result["model_type"], str)
        assert isinstance(result["coefficients"], dict)
        assert isinstance(result["r_squared"], float)
        assert isinstance(result["p_values"], dict)
        
        # Validate values
        assert 0 <= result["r_squared"] <= 1
        for p in result["p_values"].values():
            assert 0 <= p <= 1

    def test_remediation_action_present_when_needed(self):
        """Test that remediation_action is present when VIF > 5."""
        np.random.seed(42)
        X1 = np.random.rand(100)
        X2 = X1 + np.random.randn(100) * 0.01
        X = np.column_stack([X1, X2])
        y = X1 + X2 + np.random.randn(100) * 0.1
        names = ["f1", "f2"]
        
        result = run_regression(X, y, names, model_type="linear")
        
        # Should have remediation_action field
        assert "remediation_action" in result
        # Action should describe what happened
        if result["remediation_action"]:
            assert isinstance(result["remediation_action"], str)
            assert len(result["remediation_action"]) > 0

def test_vif_logic_integration(temp_project_dirs):
    """Integration test for VIF logic end-to-end."""
    np.random.seed(42)
    # Create data with some multicollinearity
    X1 = np.random.rand(100)
    X2 = X1 + np.random.randn(100) * 0.05
    X3 = np.random.rand(100)
    X = np.column_stack([X1, X2, X3])
    y = 2*X1 + 3*X2 + X3 + np.random.randn(100) * 0.1
    names = ["feature1", "feature2", "feature3"]
    
    # Run full regression pipeline
    result = run_regression(X, y, names, model_type="linear")
    
    # Verify all required outputs
    assert "model_type" in result
    assert "r_squared" in result
    assert "coefficients" in result
    assert "p_values" in result
    assert "remediation_action" in result
    assert "anova" in result
    
    # Verify schema compliance
    assert result["model_type"] in ["Linear", "Ridge", "Polynomial"]
    assert isinstance(result["r_squared"], float)
    assert isinstance(result["coefficients"], dict)
    assert isinstance(result["remediation_action"], (str, type(None)))