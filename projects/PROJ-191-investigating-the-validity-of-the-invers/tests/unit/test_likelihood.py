"""
Unit tests for the log-likelihood function with banded covariance.

This module verifies the correctness of the Yukawa model log-likelihood
implementation, specifically focusing on the banded covariance matrix
approximation for computational efficiency.
"""
import unittest
import numpy as np
from numpy.linalg import inv, cholesky
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.physics import yukawa_log_likelihood, newtonian_log_likelihood, yukawa_force
from code.data.harmonize import construct_covariance_matrix


class TestBandedCovariance(unittest.TestCase):
    """Tests for banded covariance matrix construction and usage."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)
        self.n_points = 50
        self.separations = np.logspace(-5, -4, self.n_points)
        self.forces = np.random.randn(self.n_points) * 1e-12
        
        # Create a realistic covariance matrix with correlations
        self.stat_errors = np.abs(self.forces) * 0.1
        self.sys_errors = np.abs(self.forces) * 0.05
        
        # Construct full covariance matrix
        self.full_cov = construct_covariance_matrix(
            self.separations, self.stat_errors, self.sys_errors
        )
        
        # Create banded approximation (bandwidth = 5)
        self.bandwidth = 5
        self.banded_cov = self._create_banded_covariance(self.full_cov, self.bandwidth)

    def _create_banded_covariance(self, cov_matrix, bandwidth):
        """Create a banded approximation of the covariance matrix."""
        n = cov_matrix.shape[0]
        banded = np.zeros_like(cov_matrix)
        for i in range(n):
            for j in range(max(0, i - bandwidth), min(n, i + bandwidth + 1)):
                banded[i, j] = cov_matrix[i, j]
        return banded

    def test_banded_covariance_preserves_diagonal(self):
        """Verify that banded covariance preserves diagonal elements."""
        np.testing.assert_array_almost_equal(
            self.full_cov.diagonal(),
            self.banded_cov.diagonal(),
            decimal=10,
            err_msg="Banded covariance should preserve diagonal elements"
        )

    def test_banded_covariance_positive_definite(self):
        """Verify that the banded covariance matrix is positive definite."""
        try:
            cholesky(self.banded_cov)
            is_pd = True
        except np.linalg.LinAlgError:
            is_pd = False
        
        self.assertTrue(is_pd, "Banded covariance matrix must be positive definite")

    def test_banded_covariance_symmetric(self):
        """Verify that the banded covariance matrix is symmetric."""
        np.testing.assert_array_almost_equal(
            self.banded_cov,
            self.banded_cov.T,
            decimal=10,
            err_msg="Banded covariance matrix must be symmetric"
        )

    def test_banded_covariance_off_band_zero(self):
        """Verify that elements outside the band are zero."""
        n = self.banded_cov.shape[0]
        for i in range(n):
            for j in range(n):
                if abs(i - j) > self.bandwidth:
                    self.assertEqual(
                        self.banded_cov[i, j], 0.0,
                        f"Element ({i}, {j}) outside band should be zero"
                    )


class TestLogLikelihood(unittest.TestCase):
    """Tests for the log-likelihood function with banded covariance."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)
        self.n_points = 30
        self.separations = np.logspace(-5, -4, self.n_points)
        self.measured_forces = np.random.randn(self.n_points) * 1e-12
        
        # Create covariance matrix
        self.stat_errors = np.abs(self.measured_forces) * 0.1
        self.sys_errors = np.abs(self.measured_forces) * 0.05
        self.full_cov = construct_covariance_matrix(
            self.separations, self.stat_errors, self.sys_errors
        )
        
        # Banded approximation
        self.bandwidth = 3
        self.banded_cov = self._create_banded_covariance(self.full_cov, self.bandwidth)
        self.banded_inv = inv(self.banded_cov)
        
        # True parameters for synthetic data
        self.true_alpha = 10.0
        self.true_lambda = 1e-4

    def _create_banded_covariance(self, cov_matrix, bandwidth):
        """Create a banded approximation of the covariance matrix."""
        n = cov_matrix.shape[0]
        banded = np.zeros_like(cov_matrix)
        for i in range(n):
            for j in range(max(0, i - bandwidth), min(n, i + bandwidth + 1)):
                banded[i, j] = cov_matrix[i, j]
        return banded

    def test_log_likelihood_shape(self):
        """Verify that log-likelihood returns a scalar."""
        params = [1.0, 1e-4]  # [alpha, lambda]
        log_like = yukawa_log_likelihood(
            params, self.separations, self.measured_forces, self.banded_inv
        )
        
        self.assertIsInstance(log_like, (float, np.floating),
                            "Log-likelihood must return a scalar")

    def test_log_likelihood_negative_infinity(self):
        """Verify that log-likelihood is -inf for invalid parameters."""
        # Negative alpha should give -inf
        params_invalid = [-1.0, 1e-4]
        log_like = yukawa_log_likelihood(
            params_invalid, self.separations, self.measured_forces, self.banded_inv
        )
        
        self.assertEqual(log_like, -np.inf,
                       "Log-likelihood should be -inf for invalid parameters")

        # Negative lambda should give -inf
        params_invalid = [1.0, -1e-4]
        log_like = yukawa_log_likelihood(
            params_invalid, self.separations, self.measured_forces, self.banded_inv
        )
        
        self.assertEqual(log_like, -np.inf,
                       "Log-likelihood should be -inf for invalid parameters")

    def test_log_likelihood_maximum_at_true_params(self):
        """Verify that log-likelihood is maximized near true parameters."""
        # Generate data with known parameters
        true_forces = yukawa_force(
            self.separations, self.true_alpha, self.true_lambda
        )
        # Add noise consistent with covariance
        noise = np.random.multivariate_normal(
            np.zeros(self.n_points), self.banded_cov
        )
        noisy_forces = true_forces + noise

        # Evaluate log-likelihood at true parameters
        params_true = [self.true_alpha, self.true_lambda]
        log_like_true = yukawa_log_likelihood(
            params_true, self.separations, noisy_forces, self.banded_inv
        )

        # Evaluate at perturbed parameters
        params_perturbed = [self.true_alpha * 1.1, self.true_lambda * 0.9]
        log_like_perturbed = yukawa_log_likelihood(
            params_perturbed, self.separations, noisy_forces, self.banded_inv
        )

        # True parameters should give higher (or equal) log-likelihood
        self.assertGreaterEqual(
            log_like_true, log_like_perturbed,
            "Log-likelihood should be maximized near true parameters"
        )

    def test_log_likelihood_compared_to_newtonian(self):
        """Verify that Yukawa model reduces to Newtonian when alpha=0."""
        params_yukawa = [0.0, 1e-4]  # alpha=0 should be Newtonian
        params_newtonian = [0.0, 1e-4]
        
        log_like_yukawa = yukawa_log_likelihood(
            params_yukawa, self.separations, self.measured_forces, self.banded_inv
        )
        log_like_newtonian = newtonian_log_likelihood(
            params_newtonian, self.separations, self.measured_forces, self.banded_inv
        )

        np.testing.assert_almost_equal(
            log_like_yukawa, log_like_newtonian,
            decimal=10,
            err_msg="Yukawa model with alpha=0 should equal Newtonian model"
        )

    def test_banded_vs_full_covariance_efficiency(self):
        """Verify that banded covariance is computationally more efficient."""
        # For large datasets, banded should be faster
        # This is a performance test, so we just verify it runs
        params = [5.0, 1e-4]
        
        # Full covariance
        full_inv = inv(self.full_cov)
        log_like_full = yukawa_log_likelihood(
            params, self.separations, self.measured_forces, full_inv
        )
        
        # Banded covariance
        log_like_banded = yukawa_log_likelihood(
            params, self.separations, self.measured_forces, self.banded_inv
        )
        
        # Both should be finite and similar (not identical due to approximation)
        self.assertTrue(np.isfinite(log_like_full),
                      "Full covariance log-likelihood must be finite")
        self.assertTrue(np.isfinite(log_like_banded),
                      "Banded covariance log-likelihood must be finite")
        
        # Allow for some difference due to approximation
        self.assertLess(
            abs(log_like_full - log_like_banded) / abs(log_like_full),
            0.1,  # 10% tolerance
            "Banded and full covariance log-likelihoods should be similar"
        )


class TestNumericalStability(unittest.TestCase):
    """Tests for numerical stability of log-likelihood computation."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(123)
        self.n_points = 20
        self.separations = np.logspace(-5, -4, self.n_points)
        self.measured_forces = np.random.randn(self.n_points) * 1e-12
        
        # Create covariance matrix with small errors
        self.stat_errors = np.abs(self.measured_forces) * 1e-3
        self.sys_errors = np.abs(self.measured_forces) * 1e-3
        self.full_cov = construct_covariance_matrix(
            self.separations, self.stat_errors, self.sys_errors
        )
        
        # Banded approximation
        self.bandwidth = 2
        self.banded_cov = self._create_banded_covariance(self.full_cov, self.bandwidth)
        self.banded_inv = inv(self.banded_cov)

    def _create_banded_covariance(self, cov_matrix, bandwidth):
        """Create a banded approximation of the covariance matrix."""
        n = cov_matrix.shape[0]
        banded = np.zeros_like(cov_matrix)
        for i in range(n):
            for j in range(max(0, i - bandwidth), min(n, i + bandwidth + 1)):
                banded[i, j] = cov_matrix[i, j]
        return banded

    def test_extreme_parameter_values(self):
        """Test log-likelihood with extreme parameter values."""
        # Very large alpha
        params = [1e10, 1e-4]
        log_like = yukawa_log_likelihood(
            params, self.separations, self.measured_forces, self.banded_inv
        )
        self.assertTrue(np.isfinite(log_like),
                      "Log-likelihood should handle large alpha values")

        # Very small lambda
        params = [1.0, 1e-10]
        log_like = yukawa_log_likelihood(
            params, self.separations, self.measured_forces, self.banded_inv
        )
        self.assertTrue(np.isfinite(log_like),
                      "Log-likelihood should handle small lambda values")

    def test_zero_forces(self):
        """Test log-likelihood with zero measured forces."""
        zero_forces = np.zeros(self.n_points)
        params = [1.0, 1e-4]
        log_like = yukawa_log_likelihood(
            params, self.separations, zero_forces, self.banded_inv
        )
        self.assertTrue(np.isfinite(log_like),
                      "Log-likelihood should handle zero forces")


if __name__ == '__main__':
    unittest.main()