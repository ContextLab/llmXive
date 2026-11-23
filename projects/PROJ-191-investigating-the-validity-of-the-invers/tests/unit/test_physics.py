"""
Unit tests for physics models.

Tests Newtonian and Yukawa force calculations.
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.physics import newtonian_force, yukawa_force, log_likelihood_newtonian, log_likelihood_yukawa, G, M_SOURCE, M_TEST


class TestNewtonianForce:
    """Tests for Newtonian gravitational force."""

    def test_newtonian_force_single_value(self):
        """Test Newtonian force calculation for a single separation."""
        r = 1e-3  # 1 mm
        expected = G * M_SOURCE * M_TEST / (r ** 2)
        result = newtonian_force(r)
        np.testing.assert_almost_equal(result, expected, decimal=15)

    def test_newtonian_force_array(self):
        """Test Newtonian force calculation for an array of separations."""
        r = np.array([1e-4, 2e-4, 5e-4])
        expected = G * M_SOURCE * M_TEST / (r ** 2)
        result = newtonian_force(r)
        np.testing.assert_array_almost_equal(result, expected, decimal=15)

    def test_newtonian_force_inverse_square(self):
        """Test that doubling distance reduces force by factor of 4."""
        r1 = 1e-4
        r2 = 2e-4
        f1 = newtonian_force(r1)
        f2 = newtonian_force(r2)
        np.testing.assert_almost_equal(f1 / f2, 4.0, decimal=10)

    def test_newtonian_force_zero_prevention(self):
        """Test that zero separation doesn't cause division by zero."""
        r = 0.0
        result = newtonian_force(r)
        assert np.isfinite(result)
        assert result > 0


class TestYukawaForce:
    """Tests for Yukawa-modified gravitational force."""

    def test_yukawa_force_alpha_zero(self):
        """Test that Yukawa force equals Newtonian when alpha=0."""
        r = np.array([1e-4, 2e-4, 5e-4])
        lambda_val = 1e-4
        alpha = 0.0
        
        f_yuk = yukawa_force(r, alpha, lambda_val)
        f_newt = newtonian_force(r)
        
        np.testing.assert_array_almost_equal(f_yuk, f_newt, decimal=15)

    def test_yukawa_force_positive_alpha(self):
        """Test that positive alpha increases force at short distances."""
        r = 1e-4
        lambda_val = 1e-4
        alpha = 1.0
        
        f_yuk = yukawa_force(r, alpha, lambda_val)
        f_newt = newtonian_force(r)
        
        # At r = lambda, correction should be 1 + alpha * exp(-1)
        expected_correction = 1 + alpha * np.exp(-1)
        expected_force = f_newt * expected_correction
        
        np.testing.assert_almost_equal(f_yuk, expected_force, decimal=10)

    def test_yukawa_force_large_lambda(self):
        """Test that large lambda approximates Newtonian gravity."""
        r = np.array([1e-4, 2e-4, 5e-4])
        lambda_val = 1.0  # Very large compared to r
        alpha = 1.0
        
        f_yuk = yukawa_force(r, alpha, lambda_val)
        f_newt = newtonian_force(r)
        
        # For large lambda, exp(-r/lambda) ≈ 1 - r/lambda ≈ 1
        # So correction ≈ 1 + alpha
        np.testing.assert_array_almost_equal(f_yuk / f_newt, 1 + alpha, decimal=10)

    def test_yukawa_force_small_lambda(self):
        """Test that small lambda makes correction negligible at large r."""
        r = np.array([1e-4, 2e-4, 5e-4])
        lambda_val = 1e-6  # Very small
        alpha = 1.0
        
        f_yuk = yukawa_force(r, alpha, lambda_val)
        f_newt = newtonian_force(r)
        
        # For small lambda, exp(-r/lambda) ≈ 0 at these distances
        np.testing.assert_array_almost_equal(f_yuk, f_newt, decimal=15)


class TestLogLikelihood:
    """Tests for log-likelihood functions."""

    def test_log_likelihood_newtonian_perfect_fit(self):
        """Test Newtonian log-likelihood with perfect fit."""
        r = np.array([1e-4, 2e-4, 5e-4])
        f = newtonian_force(r)
        sigma = 1e-15
        
        ll = log_likelihood_newtonian(r, f, sigma)
        
        # With perfect fit, residuals are 0
        # ll = -0.5 * sum(log(2*pi*sigma^2))
        expected = -0.5 * len(r) * (np.log(2 * np.pi * sigma ** 2))
        np.testing.assert_almost_equal(ll, expected, decimal=10)

    def test_log_likelihood_yukawa_perfect_fit(self):
        """Test Yukawa log-likelihood with perfect fit."""
        r = np.array([1e-4, 2e-4, 5e-4])
        alpha_true, lambda_true = 1.0, 1e-4
        f = yukawa_force(r, alpha_true, lambda_true)
        sigma = 1e-15
        
        ll = log_likelihood_yukawa(np.array([alpha_true, lambda_true]), r, f, sigma)
        
        # With perfect fit, residuals are 0
        expected = -0.5 * len(r) * (np.log(2 * np.pi * sigma ** 2))
        np.testing.assert_almost_equal(ll, expected, decimal=10)

    def test_log_likelihood_worse_fit(self):
        """Test that worse fit gives lower log-likelihood."""
        r = np.array([1e-4, 2e-4, 5e-4])
        f = newtonian_force(r)
        sigma = 1e-15
        
        ll_perfect = log_likelihood_newtonian(r, f, sigma)
        
        # Add noise to make fit worse
        f_noisy = f + np.array([1e-16, 1e-16, 1e-16])
        ll_worse = log_likelihood_newtonian(r, f_noisy, sigma)
        
        assert ll_worse < ll_perfect