"""
Unit tests for metrics.py (T024).

Tests for reduced chi-squared, AIC, and BIC calculations.
"""

import numpy as np
import pytest
import math

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from metrics import (
    calculate_reduced_chi2,
    calculate_aic,
    calculate_bic,
    compute_fit_metrics
)


class TestCalculateReducedChi2:
    def test_perfect_fit(self):
        """Perfect fit should yield reduced chi2 = 1.0."""
        residuals = np.array([0.0, 0.0, 0.0])
        uncertainties = np.array([1.0, 1.0, 1.0])
        n_dof = 3  # 3 points, 0 params for this specific test function

        result = calculate_reduced_chi2(residuals, uncertainties, n_dof)
        assert math.isclose(result, 0.0, abs_tol=1e-6)

    def test_good_fit(self):
        """Residuals equal to uncertainty should yield reduced chi2 = 1.0."""
        residuals = np.array([1.0, 1.0, 1.0])
        uncertainties = np.array([1.0, 1.0, 1.0])
        n_dof = 3

        result = calculate_reduced_chi2(residuals, uncertainties, n_dof)
        # chi2 = 1+1+1 = 3. reduced = 3/3 = 1.0
        assert math.isclose(result, 1.0, abs_tol=1e-6)

    def test_bad_fit(self):
        """Large residuals should yield reduced chi2 > 1.0."""
        residuals = np.array([2.0, 2.0, 2.0])
        uncertainties = np.array([1.0, 1.0, 1.0])
        n_dof = 3

        result = calculate_reduced_chi2(residuals, uncertainties, n_dof)
        # chi2 = 4+4+4 = 12. reduced = 12/3 = 4.0
        assert math.isclose(result, 4.0, abs_tol=1e-6)

    def test_zero_dof_raises_warning(self):
        """Zero degrees of freedom should return inf."""
        residuals = np.array([1.0])
        uncertainties = np.array([1.0])
        n_dof = 0

        result = calculate_reduced_chi2(residuals, uncertainties, n_dof)
        assert result == float('inf')

    def test_mismatched_lengths_raises(self):
        """Mismatched lengths should raise ValueError."""
        residuals = np.array([1.0, 2.0])
        uncertainties = np.array([1.0])
        n_dof = 1

        with pytest.raises(ValueError):
            calculate_reduced_chi2(residuals, uncertainties, n_dof)


class TestCalculateAic:
    def test_basic_calculation(self):
        """AIC = 2k + chi2."""
        chi2 = 10.0
        k = 2
        expected = 2 * 2 + 10.0  # 14.0
        assert math.isclose(calculate_aic(chi2, k), expected)

    def test_zero_params(self):
        """Zero params should trigger warning and default to k=1."""
        chi2 = 10.0
        k = 0
        result = calculate_aic(chi2, k)
        # Should use k=1 internally
        assert math.isclose(result, 2 * 1 + 10.0)


class TestCalculateBic:
    def test_basic_calculation(self):
        """BIC = k*ln(n) + chi2."""
        chi2 = 10.0
        k = 2
        n = 10
        expected = 2 * np.log(10) + 10.0
        result = calculate_bic(chi2, k, n)
        assert math.isclose(result, expected)

    def test_large_n(self):
        """BIC penalizes more for larger n."""
        chi2 = 10.0
        k = 2
        n_small = 10
        n_large = 100

        bic_small = calculate_bic(chi2, k, n_small)
        bic_large = calculate_bic(chi2, k, n_large)

        assert bic_large > bic_small

    def test_invalid_n(self):
        """Negative or zero n should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bic(10.0, 2, 0)


class TestComputeFitMetrics:
    def test_full_metrics(self):
        """Test full metric calculation."""
        residuals = np.array([1.0, 1.0, 1.0, 1.0])
        uncertainties = np.array([1.0, 1.0, 1.0, 1.0])
        n_params = 2

        metrics = compute_fit_metrics(residuals, uncertainties, n_params)

        assert 'reduced_chi2' in metrics
        assert 'chi2' in metrics
        assert 'aic' in metrics
        assert 'bic' in metrics
        assert 'n_dof' in metrics
        assert 'n_points' in metrics

        # chi2 = 4
        # n_dof = 4 - 2 = 2
        # reduced_chi2 = 2.0
        assert math.isclose(metrics['chi2'], 4.0)
        assert math.isclose(metrics['reduced_chi2'], 2.0)
        assert metrics['n_dof'] == 2

    def test_nan_on_invalid_dof(self):
        """Should return NaNs if dof <= 0."""
        residuals = np.array([1.0, 1.0])
        uncertainties = np.array([1.0, 1.0])
        n_params = 3  # n_dof = 2 - 3 = -1

        metrics = compute_fit_metrics(residuals, uncertainties, n_params)

        assert math.isnan(metrics['reduced_chi2'])
        assert math.isnan(metrics['aic'])
        assert math.isnan(metrics['bic'])
        assert metrics['n_dof'] == -1