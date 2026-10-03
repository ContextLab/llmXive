"""
Unit tests for the metrics calculator.

Tests for reduced chi-squared, AIC, and BIC calculations.
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import (
    calculate_reduced_chi2,
    calculate_aic,
    calculate_bic,
    compute_fit_metrics
)


class TestCalculateReducedChi2:
    def test_basic_calculation(self):
        """Test basic reduced chi2 calculation."""
        residuals = np.array([0.0, 0.0, 0.0])
        uncertainties = np.array([1.0, 1.0, 1.0])
        dof = 3 - 0  # 3 points, 0 params (just for testing)

        result = calculate_reduced_chi2(residuals, uncertainties, dof)
        assert result == 0.0

    def test_non_zero_residuals(self):
        """Test with non-zero residuals."""
        residuals = np.array([1.0, 1.0, 1.0])
        uncertainties = np.array([1.0, 1.0, 1.0])
        dof = 3

        result = calculate_reduced_chi2(residuals, uncertainties, dof)
        expected = 1.0  # sum(1^2/1^2) / 3 = 3/3 = 1
        assert np.isclose(result, expected)

    def test_zero_uncertainty_handling(self):
        """Test that zero uncertainty is handled (replaced with epsilon)."""
        residuals = np.array([1.0])
        uncertainties = np.array([0.0])
        dof = 1

        result = calculate_reduced_chi2(residuals, uncertainties, dof)
        # Should not crash, should use epsilon
        assert np.isfinite(result)

    def test_invalid_dof(self):
        """Test that invalid degrees of freedom returns infinity."""
        residuals = np.array([1.0])
        uncertainties = np.array([1.0])
        dof = 0

        result = calculate_reduced_chi2(residuals, uncertainties, dof)
        assert result == float('inf')

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        residuals = np.array([1.0, 2.0])
        uncertainties = np.array([1.0])
        dof = 1

        with pytest.raises(ValueError):
            calculate_reduced_chi2(residuals, uncertainties, dof)


class TestCalculateAic:
    def test_basic_calculation(self):
        """Test basic AIC calculation."""
        chi2 = 10.0
        k = 2

        result = calculate_aic(chi2, k)
        expected = 2 * 2 + 10.0  # 4 + 10 = 14
        assert result == expected

    def test_zero_k_handling(self):
        """Test that zero k is handled (replaced with 1)."""
        chi2 = 10.0
        k = 0

        result = calculate_aic(chi2, k)
        expected = 2 * 1 + 10.0  # 2 + 10 = 12
        assert result == expected


class TestCalculateBic:
    def test_basic_calculation(self):
        """Test basic BIC calculation."""
        chi2 = 10.0
        k = 2
        n = 100

        result = calculate_bic(chi2, k, n)
        # BIC = k * ln(n) + chi2 = 2 * ln(100) + 10
        expected = 2 * np.log(100) + 10.0
        assert np.isclose(result, expected)

    def test_zero_k_handling(self):
        """Test that zero k is handled (replaced with 1)."""
        chi2 = 10.0
        k = 0
        n = 100

        result = calculate_bic(chi2, k, n)
        expected = 1 * np.log(100) + 10.0
        assert np.isclose(result, expected)

    def test_invalid_n(self):
        """Test that invalid n raises an error."""
        chi2 = 10.0
        k = 2
        n = 0

        with pytest.raises(ValueError):
            calculate_bic(chi2, k, n)


class TestComputeFitMetrics:
    def test_full_metrics(self):
        """Test full metrics computation."""
        residuals = np.array([1.0, 1.0, 1.0, 1.0])
        uncertainties = np.array([1.0, 1.0, 1.0, 1.0])
        n_params = 2

        result = compute_fit_metrics(residuals, uncertainties, n_params)

        assert 'reduced_chi2' in result
        assert 'chi2' in result
        assert 'aic' in result
        assert 'bic' in result
        assert 'n_dof' in result
        assert 'n_points' in result

        # Check values
        # chi2 = sum(1^2/1^2) = 4
        # dof = 4 - 2 = 2
        # reduced_chi2 = 4/2 = 2
        assert np.isclose(result['chi2'], 4.0)
        assert result['n_dof'] == 2
        assert np.isclose(result['reduced_chi2'], 2.0)

    def test_invalid_dof(self):
        """Test behavior when dof <= 0."""
        residuals = np.array([1.0, 1.0])
        uncertainties = np.array([1.0, 1.0])
        n_params = 5  # More params than points

        result = compute_fit_metrics(residuals, uncertainties, n_params)

        assert np.isnan(result['reduced_chi2'])
        assert np.isnan(result['chi2'])
        assert np.isnan(result['aic'])
        assert np.isnan(result['bic'])
        assert result['n_dof'] == -3  # 2 - 5
        assert result['n_points'] == 2