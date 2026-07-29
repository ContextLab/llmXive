"""
Unit tests for code/analysis/metrics.py

These tests verify the correctness of metric calculations:
Condition Number, VIF, Empirical Power, and False Discovery Rate.
"""
import numpy as np
import pandas as pd
import pytest
from typing import Tuple

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
        assert np.isclose(cond_num, 1.0, atol=1e-5), "Identity matrix should have condition number 1"

    def test_condition_number_collinear(self):
        """Test condition number for a near-collinear matrix."""
        # Create a matrix with high collinearity
        X = np.random.randn(100, 5)
        X[:, 1] = X[:, 0] * 0.999 + np.random.randn(100) * 0.001
        cond_num = calculate_condition_number(X)
        assert cond_num > 100, "Collinear matrix should have high condition number"


class TestVIF:
    """Tests for Variance Inflation Factor calculation."""

    def test_vif_no_collinearity(self):
        """Test VIF for independent variables."""
        X = np.random.randn(100, 5)
        # Add intercept manually or assume function handles it
        vif_values = calculate_vif(X)
        # VIF for independent vars should be close to 1
        assert all(v < 2 for v in vif_values), "VIF for independent variables should be close to 1"

    def test_vif_high_collinearity(self):
        """Test VIF for highly collinear variables."""
        X = np.random.randn(100, 5)
        X[:, 1] = X[:, 0] * 0.99  # High correlation
        vif_values = calculate_vif(X)
        # One of the VIFs should be high
        assert any(v > 10 for v in vif_values), "High collinearity should result in high VIF"


class TestEmpiricalPower:
    """Tests for Empirical Power calculation."""

    def test_power_perfect_selection(self):
        """Test power when all true non-zero coefficients are selected and significant."""
        true_coeffs = np.array([1.0, 1.0, 1.0, 0.0, 0.0])
        # All true non-zero are selected and significant
        selected_mask = np.array([True, True, True, False, False])
        significant_mask = np.array([True, True, True, False, False])

        power = calculate_empirical_power(true_coeffs, selected_mask, significant_mask)
        assert power == 1.0, "Perfect selection should yield power of 1.0"

    def test_power_zero_true_nonzero(self):
        """Test power when there are no true non-zero coefficients."""
        true_coeffs = np.array([0.0, 0.0, 0.0])
        selected_mask = np.array([False, False, False])
        significant_mask = np.array([False, False, False])

        power = calculate_empirical_power(true_coeffs, selected_mask, significant_mask)
        # Power is undefined or 0 when denominator is 0. Usually defined as 0.
        assert power == 0.0, "Power should be 0 when no true non-zero coefficients exist"

    def test_power_partial_selection(self):
        """Test power with partial selection of true non-zero coefficients."""
        true_coeffs = np.array([1.0, 1.0, 1.0, 0.0, 0.0])
        # Only 2 out of 3 true non-zero are selected
        selected_mask = np.array([True, True, False, False, False])
        significant_mask = np.array([True, True, False, False, False])

        power = calculate_empirical_power(true_coeffs, selected_mask, significant_mask)
        assert power == 2.0 / 3.0, "Power should be 2/3 for partial selection"


class TestFalseDiscoveryRate:
    """Tests for False Discovery Rate calculation."""

    def test_fdr_zero_false_discoveries(self):
        """Test FDR when there are no false discoveries."""
        true_coeffs = np.array([1.0, 1.0, 0.0, 0.0])
        selected_mask = np.array([True, True, False, False])
        significant_mask = np.array([True, True, False, False])

        fdr = calculate_false_discovery_rate(true_coeffs, selected_mask, significant_mask)
        assert fdr == 0.0, "FDR should be 0 when no false discoveries"

    def test_fdr_all_false_discoveries(self):
        """Test FDR when all selected are false discoveries."""
        true_coeffs = np.array([0.0, 0.0, 0.0, 0.0])
        selected_mask = np.array([True, True, False, False])
        significant_mask = np.array([True, True, False, False])

        fdr = calculate_false_discovery_rate(true_coeffs, selected_mask, significant_mask)
        assert fdr == 1.0, "FDR should be 1.0 when all selected are false discoveries"

    def test_fdr_mixed(self):
        """Test FDR with mixed true and false discoveries."""
        true_coeffs = np.array([1.0, 0.0, 0.0, 0.0])
        selected_mask = np.array([True, True, False, False])
        significant_mask = np.array([True, True, False, False])

        fdr = calculate_false_discovery_rate(true_coeffs, selected_mask, significant_mask)
        # 1 true positive, 1 false positive -> FDR = 1/2 = 0.5
        assert fdr == 0.5, "FDR should be 0.5 for 1 TP and 1 FP"