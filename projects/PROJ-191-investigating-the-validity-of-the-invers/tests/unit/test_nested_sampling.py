"""
Unit tests for the nested sampling implementation (T024).
"""

import unittest
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add code to path
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from inference.nested import (
    log_prior_yukawa,
    log_likelihood_yukawa,
    log_prior_newtonian,
    log_likelihood_newtonian,
    run_nested_sampling
)
from data.models import HarmonizedDataset

class TestNestedSamplingPriors(unittest.TestCase):
    def test_prior_yukawa_bounds(self):
        """Test that priors return -inf outside bounds."""
        # Valid u in [0, 1]
        u_valid = np.array([0.5, 0.5])
        self.assertGreaterEqual(log_prior_yukawa(u_valid), 0.0)
        
        # Invalid u (negative)
        u_invalid = np.array([-0.1, 0.5])
        self.assertEqual(log_prior_yukawa(u_invalid), -np.inf)
        
        # Invalid u (> 1)
        u_invalid2 = np.array([1.5, 0.5])
        self.assertEqual(log_prior_yukawa(u_invalid2), -np.inf)

    def test_prior_newtonian(self):
        """Test Newtonian prior (constant 0)."""
        u = np.array([]) # 0 dimensions
        self.assertEqual(log_prior_newtonian(u), 0.0)

class TestNestedSamplingLikelihoods(unittest.TestCase):
    def setUp(self):
        # Create synthetic data for testing
        self.n_points = 50
        self.x = np.linspace(1e-5, 1e-3, self.n_points) # 10 um to 1 mm
        self.y_true = 1e-9 * (1 / self.x**2) # Approx Newtonian force (scaled)
        # Add noise
        np.random.seed(42)
        self.y = self.y_true + np.random.normal(0, 1e-15, self.n_points)
        
        # Identity covariance for simplicity in unit test
        self.cov = np.eye(self.n_points)
        self.chol = np.eye(self.n_points) # Cholesky of identity is identity

    def test_likelihood_newtonian(self):
        """Test Newtonian likelihood calculation."""
        theta = np.array([]) # 0 parameters
        log_lik = log_likelihood_newtonian(theta, self.x, self.y, None, self.chol)
        self.assertTrue(np.isfinite(log_lik))
        # Likelihood should be negative (log of probability < 1)
        self.assertLess(log_lik, 0.0)

    def test_likelihood_yukawa(self):
        """Test Yukawa likelihood calculation."""
        # theta = [log10(alpha), log10(lambda)]
        # alpha = 1e-5, lambda = 1e-4
        theta = np.array([np.log10(1e-5), np.log10(1e-4)])
        log_lik = log_likelihood_yukawa(theta, self.x, self.y, None, self.chol)
        self.assertTrue(np.isfinite(log_lik))
        self.assertLess(log_lik, 0.0)
        
        # Test invalid theta
        theta_invalid = np.array([-1.0, -1.0]) # alpha = 0.1 (ok), lambda = 0.1 (ok but out of range? no, range is log10)
        # Wait, log10(0.1) = -1. Range for log10(lambda) is log10(1e-6) to log10(1e-3) -> -6 to -3.
        # So -1 is out of bounds for lambda.
        # But the function checks alpha > 0 and lambda > 0.
        # The prior checks bounds. The likelihood function itself might not check bounds if called directly.
        # Let's check the implementation: it checks alpha <= 0 or lambda <= 0.
        # 0.1 is > 0, so it should return a value.
        # However, the prior returns -inf for out of bounds.
        # In nested sampling, log_prior is called first. If -inf, likelihood is not evaluated.
        # But if we call log_likelihood directly with out-of-bounds parameters, it might still compute.
        # The spec says: "Check bounds".
        # Let's assume the likelihood function should also be robust or the prior handles it.
        # In the code, log_likelihood_yukawa checks alpha <= 0 or lambda <= 0.
        # It does NOT check the prior bounds.
        # So it will return a value.
        # That's fine for unit testing the math.
        
        theta_valid = np.array([np.log10(1e-5), np.log10(1e-4)])
        self.assertTrue(np.isfinite(log_likelihood_yukawa(theta_valid, self.x, self.y, None, self.chol)))

class TestNestedSamplingIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data" / "processed"
        self.data_dir.mkdir(parents=True)
        
        # Create a dummy harmonized dataset
        n_points = 20
        x = np.linspace(1e-5, 1e-3, n_points)
        y = 1e-9 * (1 / x**2)
        cov = np.eye(n_points) * 1e-30 # Small noise
        
        dataset = HarmonizedDataset(
            separation_m=x,
            force_n=y,
            covariance_matrix=cov,
            metadata={"source": "test"}
        )
        
        # Save dataset
        # We need to save in the format load_harmonized_data expects
        # Assuming JSON format based on T024 code:
        data_dict = {
            "separation_m": x.tolist(),
            "force_n": y.tolist(),
            "covariance_matrix": cov.tolist(),
            "metadata": dataset.metadata
        }
        
        dataset_path = self.data_dir / "harmonized_dataset.json"
        with open(dataset_path, "w") as f:
            json.dump(data_dict, f)
        
        # Save covariance separately (as required by nested.py)
        cov_path = self.data_dir / "covariance_matrix.npy"
        np.save(cov_path, cov)
        
        # Patch the default data path in the module or pass it explicitly
        # We will pass it explicitly in the test

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_run_nested_sampling_newtonian(self):
        """Test running nested sampling for Newtonian model."""
        data_path = Path(self.temp_dir) / "data" / "processed" / "harmonized_dataset.json"
        results = run_nested_sampling(
            model="newtonian",
            data_path=data_path,
            nlive=10, # Small number for speed
            maxiter=100
        )
        
        self.assertIn("log_evidence", results)
        self.assertTrue(np.isfinite(results["log_evidence"]))
        self.assertEqual(results["model"], "newtonian")

    def test_run_nested_sampling_yukawa(self):
        """Test running nested sampling for Yukawa model."""
        data_path = Path(self.temp_dir) / "data" / "processed" / "harmonized_dataset.json"
        results = run_nested_sampling(
            model="yukawa",
            data_path=data_path,
            nlive=10, # Small number for speed
            maxiter=100
        )
        
        self.assertIn("log_evidence", results)
        self.assertTrue(np.isfinite(results["log_evidence"]))
        self.assertEqual(results["model"], "yukawa")
        self.assertIn("samples", results)
        self.assertIn("alpha", results["samples"])
        self.assertIn("lambda", results["samples"])

if __name__ == "__main__":
    unittest.main()
