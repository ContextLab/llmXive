"""
Unit tests for the metrics calculator (T024).

Tests reduced chi-squared, AIC, and BIC calculations against known values.
"""

import numpy as np
import pytest
from pathlib import Path

# Import the functions to test
from metrics import (
    calculate_reduced_chi2,
    calculate_aic,
    calculate_bic,
    compute_fit_metrics
)

# Test fixtures
@pytest.fixture
def simple_residuals():
    return np.array([1.0, 2.0, 3.0, 4.0, 5.0])

@pytest.fixture
def simple_uncertainties():
    return np.array([1.0, 1.0, 1.0, 1.0, 1.0])

@pytest.fixture
def zero_uncertainties():
    return np.array([0.0, 0.0, 0.0])

@pytest.fixture
def perfect_fit_residuals():
    return np.array([0.0, 0.0, 0.0, 0.0])

class TestCalculateReducedChi2:
    def test_perfect_fit(self, perfect_fit_residuals, simple_uncertainties):
        """Perfect fit should yield reduced chi2 of 0."""
        n_points = len(perfect_fit_residuals)
        n_params = 2
        dof = n_points - n_params

        result = calculate_reduced_chi2(perfect_fit_residuals, simple_uncertainties, dof)
        assert result == 0.0

    def test_non_perfect_fit(self, simple_residuals, simple_uncertainties):
        """
        Residuals: [1, 2, 3, 4, 5], Unc: [1, 1, 1, 1, 1]
        Chi2 = 1^2 + 2^2 + 3^2 + 4^2 + 5^2 = 1 + 4 + 9 + 16 + 25 = 55
        N = 5, Params = 2 -> Dof = 3
        Reduced Chi2 = 55 / 3 = 18.333...
        """
        n_points = len(simple_residuals)
        n_params = 2
        dof = n_points - n_params

        result = calculate_reduced_chi2(simple_residuals, simple_uncertainties, dof)
        expected = 55.0 / 3.0
        assert np.isclose(result, expected)

    def test_invalid_dof(self, simple_residuals, simple_uncertainties):
        """Dof <= 0 should return infinity."""
        result = calculate_reduced_chi2(simple_residuals, simple_uncertainties, 0)
        assert result == float('inf')

        result = calculate_reduced_chi2(simple_residuals, simple_uncertainties, -1)
        assert result == float('inf')

    def test_length_mismatch(self):
        """Mismatched lengths should raise ValueError."""
        res = np.array([1.0, 2.0])
        unc = np.array([1.0, 1.0, 1.0])
        with pytest.raises(ValueError):
            calculate_reduced_chi2(res, unc, 1)

class TestCalculateAic:
    def test_basic_aic(self):
        """AIC = 2k + Chi2."""
        chi2 = 10.0
        k = 3
        expected = 2 * 3 + 10.0
        assert calculate_aic(chi2, k) == expected

    def test_zero_k(self):
        """Zero k should be handled (logged warning, default to 1)."""
        # We don't assert the exact log output here, just that it doesn't crash
        result = calculate_aic(10.0, 0)
        assert result == 2 * 1 + 10.0

class TestCalculateBic:
    def test_basic_bic(self):
        """BIC = k * ln(n) + Chi2."""
        chi2 = 10.0
        k = 2
        n = 10
        expected = 2 * np.log(10) + 10.0
        assert np.isclose(calculate_bic(chi2, k, n), expected)

    def test_invalid_n(self):
        """n <= 0 should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bic(10.0, 2, 0)

    def test_zero_k(self):
        """Zero k should be handled (logged warning, default to 1)."""
        result = calculate_bic(10.0, 0, 10)
        expected = 1 * np.log(10) + 10.0
        assert np.isclose(result, expected)

class TestComputeFitMetrics:
    def test_full_metrics_calculation(self, simple_residuals, simple_uncertainties):
        """Test the full pipeline returning a dict of metrics."""
        n_params = 2
        metrics = compute_fit_metrics(simple_residuals, simple_uncertainties, n_params)

        assert 'reduced_chi2' in metrics
        assert 'chi2' in metrics
        assert 'aic' in metrics
        assert 'bic' in metrics
        assert 'n_dof' in metrics
        assert 'n_points' in metrics

        # Verify counts
        assert metrics['n_points'] == 5
        assert metrics['n_dof'] == 3

        # Verify chi2 calculation (sum of squares of residuals since unc=1)
        expected_chi2 = 55.0
        assert np.isclose(metrics['chi2'], expected_chi2)

    def test_invalid_dof_handling(self):
        """Should return NaNs when dof <= 0."""
        res = np.array([1.0, 2.0])
        unc = np.array([1.0, 1.0])
        n_params = 3  # dof = 2 - 3 = -1

        metrics = compute_fit_metrics(res, unc, n_params)

        assert np.isnan(metrics['reduced_chi2'])
        assert np.isnan(metrics['chi2'])
        assert np.isnan(metrics['aic'])
        assert np.isnan(metrics['bic'])
        assert metrics['n_dof'] == -1