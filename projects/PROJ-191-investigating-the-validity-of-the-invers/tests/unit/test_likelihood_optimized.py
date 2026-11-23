"""
Unit tests for the optimized likelihood evaluation module.

These tests verify:
1. Cholesky caching works correctly.
2. Log-likelihood computation is accurate.
3. Benchmarking functionality operates as expected.
4. Error handling for invalid inputs.
"""
import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.likelihood_optimized import OptimizedLikelihoodEvaluator, optimize_likelihood_if_needed
from models.physics import newtonian_force, yukawa_force

@pytest.fixture
def sample_covariance():
    """Create a sample positive-definite covariance matrix."""
    n = 100
    # Create a random positive-definite matrix
    A = np.random.randn(n, n)
    cov = np.dot(A, A.T) + np.eye(n) * 0.1  # Ensure positive definiteness
    return cov

@pytest.fixture
def sample_data():
    """Create sample force and separation data."""
    n = 100
    separation = np.logspace(-5, -3, n)  # 10 microns to 1000 microns
    force = 1.0 / separation**2 + np.random.randn(n) * 1e-10  # Newtonian + noise
    return force, separation

@pytest.fixture
def evaluator(sample_covariance):
    """Create an OptimizedLikelihoodEvaluator instance."""
    return OptimizedLikelihoodEvaluator(sample_covariance)

class TestOptimizedLikelihoodEvaluator:
    """Tests for the OptimizedLikelihoodEvaluator class."""
    
    def test_initialization(self, sample_covariance):
        """Test that the evaluator initializes correctly."""
        evaluator = OptimizedLikelihoodEvaluator(sample_covariance)
        assert evaluator._is_initialized is True
        assert evaluator._cholesky_cache is not None
        assert evaluator._log_det_cache is not None
    
    def test_cholesky_decomposition_validity(self, sample_covariance, evaluator):
        """Test that the cached Cholesky decomposition is valid."""
        L = evaluator._cholesky_cache
        reconstructed = np.dot(L, L.T)
        np.testing.assert_array_almost_equal(reconstructed, sample_covariance, decimal=10)
    
    def test_log_likelihood_newtonian(self, evaluator, sample_data):
        """Test log-likelihood computation for Newtonian model."""
        force, separation = sample_data
        log_lh = evaluator.log_likelihood(force, separation, model="newtonian")
        assert np.isfinite(log_lh)
        assert log_lh < 0  # Log-likelihood should be negative for real data
    
    def test_log_likelihood_yukawa(self, evaluator, sample_data):
        """Test log-likelihood computation for Yukawa model."""
        force, separation = sample_data
        alpha, lambda_m = 0.05, 1e-4
        log_lh = evaluator.log_likelihood(force, separation, alpha, lambda_m, model="yukawa")
        assert np.isfinite(log_lh)
    
    def test_log_likelihood_invalid_params(self, evaluator, sample_data):
        """Test that missing parameters raise errors for Yukawa model."""
        force, separation = sample_data
        with pytest.raises(ValueError, match="alpha and lambda_m required"):
            evaluator.log_likelihood(force, separation, model="yukawa")
    
    def test_non_positive_definite_covariance(self):
        """Test handling of non-positive-definite covariance matrix."""
        # Create a non-positive-definite matrix
        cov = np.array([[1.0, 2.0], [2.0, 1.0]])  # Determinant = -3
        with pytest.raises(ValueError, match="not positive-definite"):
            OptimizedLikelihoodEvaluator(cov)
    
    def test_benchmark(self, evaluator, sample_data):
        """Test the benchmark functionality."""
        force, separation = sample_data
        results = evaluator.benchmark(force, separation, num_iterations=10)
        
        assert "avg_time_per_call_s" in results
        assert "std_time_per_call_s" in results
        assert "num_iterations" in results
        assert results["num_iterations"] == 10
        assert results["avg_time_per_call_s"] > 0

class TestOptimizeLikelihoodIfNeeded:
    """Tests for the optimize_likelihood_if_needed function."""
    
    def test_returns_evaluator_and_results(self, sample_covariance, sample_data):
        """Test that the function returns expected types."""
        force, separation = sample_data
        evaluator, results = optimize_likelihood_if_needed(
            sample_covariance, force, separation, num_iterations=10
        )
        
        assert isinstance(evaluator, OptimizedLikelihoodEvaluator)
        assert isinstance(results, dict)
        assert "avg_time_per_call_s" in results
    
    def test_output_file_written(self, sample_covariance, sample_data, tmp_path):
        """Test that benchmark results are written to file if path provided."""
        force, separation = sample_data
        output_path = tmp_path / "benchmark.json"
        
        optimize_likelihood_if_needed(
            sample_covariance, force, separation, 
            output_path=output_path, num_iterations=10
        )
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert "avg_time_per_call_s" in data

class TestNumericalAccuracy:
    """Tests for numerical accuracy of the optimized likelihood."""
    
    def test_matches_naive_implementation(self, sample_covariance, sample_data):
        """Test that optimized likelihood matches naive implementation."""
        from scipy.linalg import cholesky, cho_solve
        
        force, separation = sample_data
        alpha, lambda_m = 0.05, 1e-4
        
        # Naive implementation
        L = cholesky(sample_covariance, lower=True)
        residuals = force - yukawa_force(separation, alpha, lambda_m)
        residuals_inv = cho_solve((L, True), residuals)
        chi_sq_naive = np.dot(residuals, residuals_inv)
        log_det_naive = 2.0 * np.sum(np.log(np.diag(L)))
        n = len(force)
        log_lh_naive = -0.5 * (n * np.log(2 * np.pi) + log_det_naive + chi_sq_naive)
        
        # Optimized implementation
        evaluator = OptimizedLikelihoodEvaluator(sample_covariance)
        log_lh_opt = evaluator.log_likelihood(force, separation, alpha, lambda_m, "yukawa")
        
        # Compare
        np.testing.assert_almost_equal(log_lh_naive, log_lh_opt, decimal=10)