"""
Unit tests for the metrics calculation logic in code/analysis/metrics.py.
Focuses on edge cases and validation of power calculations.
"""
import pytest
import numpy as np
import pandas as pd
from analysis.metrics import (
    calculate_condition_number,
    calculate_vif,
    calculate_empirical_power,
    calculate_false_discovery_rate
)

class TestConditionNumber:
    """Tests for condition number calculation."""

    def test_condition_number_well_conditioned(self):
        """Test condition number for a well-conditioned matrix."""
        # Identity matrix has condition number 1
        X = np.eye(10)
        cond_num = calculate_condition_number(X)
        assert np.isclose(cond_num, 1.0, atol=1e-5)

    def test_condition_number_ill_conditioned(self):
        """Test condition number for an ill-conditioned matrix."""
        # Create a matrix with a large condition number
        X = np.array([[1, 1], [1, 1.0001]])
        cond_num = calculate_condition_number(X)
        # The condition number should be large
        assert cond_num > 1000

class TestVIF:
    """Tests for Variance Inflation Factor calculation."""

    def test_vif_no_multicollinearity(self):
        """Test VIF when there is no multicollinearity."""
        # Orthogonal features should have VIF close to 1
        X = np.random.randn(100, 5)
        # Make them orthogonal
        X, _ = np.linalg.qr(X)
        vif_values = calculate_vif(X)
        assert all(np.isclose(vif_values, 1.0, atol=1e-1))

    def test_vif_high_multicollinearity(self):
        """Test VIF when there is high multicollinearity."""
        # Create highly correlated features
        X = np.random.randn(100, 3)
        X[:, 1] = X[:, 0] * 0.99
        vif_values = calculate_vif(X)
        # At least one VIF should be large
        assert any(vif_values > 10)

class TestEmpiricalPower:
    """Tests for empirical power calculation."""

    def test_empirical_power_all_true_positives(self):
        """Test power when all true non-zero coefficients are detected."""
        true_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        selected_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        p_values = np.array([0.01, 0.5, 0.01, 0.5])
        alpha = 0.05
        
        power = calculate_empirical_power(true_coefs, selected_coefs, p_values, alpha)
        assert power == 1.0

    def test_empirical_power_no_true_positives(self):
        """Test power when no true non-zero coefficients are detected."""
        true_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        selected_coefs = np.array([0.0, 0.0, 0.0, 0.0])
        p_values = np.array([0.5, 0.5, 0.5, 0.5])
        alpha = 0.05
        
        power = calculate_empirical_power(true_coefs, selected_coefs, p_values, alpha)
        assert power == 0.0

    def test_empirical_power_partial_detection(self):
        """Test power when some true non-zero coefficients are detected."""
        true_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        selected_coefs = np.array([1.0, 0.0, 0.0, 0.0])
        p_values = np.array([0.01, 0.5, 0.5, 0.5])
        alpha = 0.05
        
        power = calculate_empirical_power(true_coefs, selected_coefs, p_values, alpha)
        # 1 out of 2 true non-zero coefficients detected
        assert power == 0.5

    def test_empirical_power_zero_true_nonzero(self):
        """Test power when there are no true non-zero coefficients."""
        true_coefs = np.array([0.0, 0.0, 0.0, 0.0])
        selected_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        p_values = np.array([0.01, 0.5, 0.01, 0.5])
        alpha = 0.05
        
        # Should handle division by zero gracefully, likely return 0 or NaN
        power = calculate_empirical_power(true_coefs, selected_coefs, p_values, alpha)
        # The function should handle this case, returning 0 or raising an error
        # We assume it returns 0 for this case
        assert power == 0.0 or np.isnan(power)

class TestFalseDiscoveryRate:
    """Tests for False Discovery Rate calculation."""

    def test_fdr_no_false_discoveries(self):
        """Test FDR when there are no false discoveries."""
        true_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        selected_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        p_values = np.array([0.01, 0.5, 0.01, 0.5])
        alpha = 0.05
        
        fdr = calculate_false_discovery_rate(true_coefs, selected_coefs, p_values, alpha)
        assert fdr == 0.0

    def test_fdr_all_false_discoveries(self):
        """Test FDR when all selected are false discoveries."""
        true_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        selected_coefs = np.array([0.0, 1.0, 0.0, 1.0]) # Selected zero true coefs
        p_values = np.array([0.5, 0.01, 0.5, 0.01])
        alpha = 0.05
        
        # In this case, we selected variables that were truly zero
        # FDR = False Positives / Total Positives
        # False Positives = 2, Total Positives = 2
        fdr = calculate_false_discovery_rate(true_coefs, selected_coefs, p_values, alpha)
        assert fdr == 1.0

    def test_fdr_partial_false_discoveries(self):
        """Test FDR with partial false discoveries."""
        true_coefs = np.array([1.0, 0.0, 1.0, 0.0])
        selected_coefs = np.array([1.0, 1.0, 0.0, 0.0])
        p_values = np.array([0.01, 0.01, 0.5, 0.5])
        alpha = 0.05
        
        # True Positives: 1 (index 0)
        # False Positives: 1 (index 1)
        # Total Positives: 2
        # FDR = 1 / 2 = 0.5
        fdr = calculate_false_discovery_rate(true_coefs, selected_coefs, p_values, alpha)
        assert fdr == 0.5

if __name__ == '__main__':
    pytest.main([__file__, '-v'])