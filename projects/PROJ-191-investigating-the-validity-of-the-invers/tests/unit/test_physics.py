"""
Unit tests for the Yukawa force model implementation.

This module tests the physics models defined in code/models/physics.py,
specifically verifying the Newtonian inverse-square law and the Yukawa
modification at sub-millimeter scales.
"""
import numpy as np
import pytest
from pathlib import Path

# Import the physics module. 
# The import path assumes the test is run from the project root or 
# with the code/ directory in sys.path.
try:
    from code.models.physics import newtonian_force, yukawa_force, log_likelihood
except ImportError:
    # Fallback for local execution if code/ is not in sys.path automatically
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.physics import newtonian_force, yukawa_force, log_likelihood


class TestNewtonianForce:
    """Tests for the standard Newtonian inverse-square law."""

    def test_force_scales_with_1_r_squared(self):
        """Verify F ~ 1/r^2 scaling."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        
        r1 = 1.0
        r2 = 2.0
        
        f1 = newtonian_force(r1, m1, m2, G)
        f2 = newtonian_force(r2, m1, m2, G)
        
        # F2 should be 1/4 of F1
        expected_ratio = 0.25
        assert np.isclose(f2 / f1, expected_ratio, rtol=1e-9)

    def test_force_positive_for_positive_masses(self):
        """Verify force is attractive (positive in our convention for magnitude)."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = 1.0
        
        f = newtonian_force(r, m1, m2, G)
        assert f > 0

    def test_force_zero_at_infinity(self):
        """Verify force approaches zero as r -> infinity."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        
        r_large = 1e10
        f = newtonian_force(r_large, m1, m2, G)
        assert f < 1e-30

    def test_vectorized_input(self):
        """Verify function handles numpy arrays."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = np.array([1.0, 2.0, 3.0])
        
        f = newtonian_force(r, m1, m2, G)
        assert isinstance(f, np.ndarray)
        assert f.shape == r.shape
        assert all(f > 0)


class TestYukawaForce:
    """Tests for the Yukawa-modified force model."""

    def test_yukawa_reduces_to_newtonian_at_alpha_zero(self):
        """Verify Yukawa model equals Newtonian when alpha=0."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = 1.0
        alpha = 0.0
        lambda_val = 1.0
        
        f_newton = newtonian_force(r, m1, m2, G)
        f_yukawa = yukawa_force(r, m1, m2, G, alpha, lambda_val)
        
        assert np.isclose(f_yukawa, f_newton, rtol=1e-9)

    def test_yukawa_reduces_to_newtonian_at_lambda_infinity(self):
        """Verify Yukawa model approaches Newtonian as lambda -> infinity."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = 1.0
        alpha = 1.0
        lambda_val = 1e10  # Very large lambda
        
        f_newton = newtonian_force(r, m1, m2, G)
        f_yukawa = yukawa_force(r, m1, m2, G, alpha, lambda_val)
        
        # exp(-r/lambda) -> 1 as lambda -> inf
        assert np.isclose(f_yukawa, f_newton, rtol=1e-4)

    def test_alpha_positive_increases_force(self):
        """Verify positive alpha increases force magnitude relative to Newtonian."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = 1.0
        alpha = 1.0
        lambda_val = 1.0
        
        f_newton = newtonian_force(r, m1, m2, G)
        f_yukawa = yukawa_force(r, m1, m2, G, alpha, lambda_val)
        
        # exp(-1) < 1, so (1 + alpha * exp(-1)) > 1
        assert f_yukawa > f_newton

    def test_alpha_negative_decreases_force(self):
        """Verify negative alpha decreases force magnitude relative to Newtonian."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = 1.0
        alpha = -0.5
        lambda_val = 1.0
        
        f_newton = newtonian_force(r, m1, m2, G)
        f_yukawa = yukawa_force(r, m1, m2, G, alpha, lambda_val)
        
        # exp(-1) > 0, so (1 - 0.5 * exp(-1)) < 1
        assert f_yukawa < f_newton

    def test_vectorized_input(self):
        """Verify function handles numpy arrays."""
        G = 6.674e-11
        m1 = 1.0
        m2 = 1.0
        r = np.array([1e-4, 5e-4, 1e-3])  # Sub-millimeter range
        alpha = 1.0
        lambda_val = 1e-3
        
        f = yukawa_force(r, m1, m2, G, alpha, lambda_val)
        assert isinstance(f, np.ndarray)
        assert f.shape == r.shape
        assert all(f > 0)


class TestLogLikelihood:
    """Tests for the log-likelihood function."""

    def test_log_likelihood_shape(self):
        """Verify log_likelihood returns a scalar."""
        # Mock data
        r_obs = np.array([1e-4, 2e-4, 3e-4])
        f_obs = np.array([1e-20, 1e-21, 1e-22])
        cov_matrix = np.eye(3) * 1e-42  # Diagonal covariance
        
        # Parameters: alpha, lambda
        params = np.array([1.0, 1e-3])
        m1, m2, G = 1.0, 1.0, 6.674e-11
        
        ll = log_likelihood(params, r_obs, f_obs, cov_matrix, m1, m2, G)
        
        assert np.isscalar(ll) or ll.shape == ()

    def test_log_likelihood_higher_for_better_fit(self):
        """Verify log-likelihood is higher when model matches data better."""
        r_obs = np.array([1e-4, 2e-4])
        # Data generated from Newtonian (alpha=0)
        true_alpha = 0.0
        true_lambda = 1.0
        m1, m2, G = 1.0, 1.0, 6.674e-11
        
        f_obs = yukawa_force(r_obs, m1, m2, G, true_alpha, true_lambda)
        cov_matrix = np.eye(2) * 1e-44
        
        # Test with correct parameters
        params_correct = np.array([0.0, 1.0])
        ll_correct = log_likelihood(params_correct, r_obs, f_obs, cov_matrix, m1, m2, G)
        
        # Test with wrong parameters
        params_wrong = np.array([10.0, 1.0])
        ll_wrong = log_likelihood(params_wrong, r_obs, f_obs, cov_matrix, m1, m2, G)
        
        assert ll_correct > ll_wrong

    def test_log_likelihood_with_covariance(self):
        """Verify log-likelihood accounts for covariance matrix."""
        r_obs = np.array([1e-4, 2e-4])
        f_obs = np.array([1e-20, 1e-21])
        m1, m2, G = 1.0, 1.0, 6.674e-11
        params = np.array([0.0, 1.0])
        
        # Small covariance
        cov_small = np.eye(2) * 1e-44
        ll_small = log_likelihood(params, r_obs, f_obs, cov_small, m1, m2, G)
        
        # Large covariance
        cov_large = np.eye(2) * 1e-30
        ll_large = log_likelihood(params, r_obs, f_obs, cov_large, m1, m2, G)
        
        # With larger covariance, the penalty for residuals is smaller,
        # so the likelihood should be higher (less negative) for the same residuals
        # Wait, actually: -0.5 * (residuals)^T * Cov^-1 * (residuals)
        # If Cov is large, Cov^-1 is small, so the penalty term is small (less negative).
        # Thus ll_large should be > ll_small (closer to 0).
        assert ll_large > ll_small

    def test_log_likelihood_nan_for_invalid_params(self):
        """Verify log_likelihood returns -inf or nan for invalid parameters."""
        r_obs = np.array([1e-4])
        f_obs = np.array([1e-20])
        cov_matrix = np.eye(1) * 1e-44
        m1, m2, G = 1.0, 1.0, 6.674e-11
        
        # Negative lambda is physically invalid
        params = np.array([1.0, -1.0])
        ll = log_likelihood(params, r_obs, f_obs, cov_matrix, m1, m2, G)
        
        assert not np.isfinite(ll) or ll == -np.inf

    def test_log_likelihood_nan_for_negative_r(self):
        """Verify log_likelihood handles negative r gracefully if passed."""
        r_obs = np.array([-1e-4])
        f_obs = np.array([1e-20])
        cov_matrix = np.eye(1) * 1e-44
        m1, m2, G = 1.0, 1.0, 6.674e-11
        params = np.array([1.0, 1.0])
        
        ll = log_likelihood(params, r_obs, f_obs, cov_matrix, m1, m2, G)
        
        # Should be -inf or nan due to division by negative r or exp of positive
        assert not np.isfinite(ll) or ll == -np.inf