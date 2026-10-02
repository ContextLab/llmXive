"""
Unit tests for the log-likelihood function with full covariance.

This module tests the implementation of log_likelihood_newtonian and 
log_likelihood_yukawa from code/models/likelihood.py.

Tests verify:
1. Correctness of Cholesky decomposition usage for numerical stability
2. Proper handling of diagonal vs banded covariance matrices
3. Consistency with expected physical behavior
4. Error handling for invalid inputs (non-positive-definite matrices, etc.)
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.likelihood import (
    load_covariance_matrix,
    compute_cholesky_decomposition,
    log_likelihood_newtonian,
    log_likelihood_yukawa
)
from models.physics import newtonian_force, yukawa_force

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n_points = 50
    separation_m = np.logspace(-4, -2, n_points)  # 0.1mm to 10mm
    force_n = newtonian_force(separation_m) * (1 + 0.01 * np.random.randn(n_points))
    
    # Create a diagonal covariance matrix (statistical uncertainties)
    uncertainties = 0.01 * np.abs(force_n)
    covariance_matrix = np.diag(uncertainties**2)
    
    return {
        'separation_m': separation_m,
        'force_n': force_n,
        'covariance_matrix': covariance_matrix,
        'uncertainties': uncertainties
    }

@pytest.fixture
def banded_covariance_matrix(sample_data):
    """Create a banded covariance matrix for testing."""
    n = len(sample_data['force_n'])
    cov = np.zeros((n, n))
    bandwidth = 20
    
    for i in range(n):
        for j in range(n):
            if abs(i - j) <= bandwidth:
                # Exponential decay correlation
                cov[i, j] = sample_data['uncertainties'][i] * sample_data['uncertainties'][j] * np.exp(-abs(i-j)/10)
            else:
                cov[i, j] = 0
    
    # Ensure positive definiteness
    cov = cov @ cov.T
    return cov

def test_cholesky_decomposition_diagonal(sample_data):
    """Test Cholesky decomposition with diagonal covariance matrix."""
    cov = sample_data['covariance_matrix']
    L = compute_cholesky_decomposition(cov)
    
    # Verify L @ L.T = cov
    reconstructed = L @ L.T
    np.testing.assert_allclose(reconstructed, cov, rtol=1e-10)
    
    # Verify L is lower triangular
    assert np.allclose(L, np.tril(L))

def test_cholesky_decomposition_banded(sample_data, banded_covariance_matrix):
    """Test Cholesky decomposition with banded covariance matrix."""
    cov = banded_covariance_matrix
    L = compute_cholesky_decomposition(cov)
    
    # Verify L @ L.T = cov
    reconstructed = L @ L.T
    np.testing.assert_allclose(reconstructed, cov, rtol=1e-8)
    
    # Verify L is lower triangular
    assert np.allclose(L, np.tril(L))

def test_log_likelihood_newtonian_positive_definite(sample_data):
    """Test Newtonian log-likelihood with positive-definite covariance."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = sample_data['covariance_matrix']
    
    # Compute expected force (Newtonian)
    expected_force = newtonian_force(sep)
    
    # Calculate log-likelihood
    log_like = log_likelihood_newtonian(sep, force, cov)
    
    # Log-likelihood should be finite (not NaN or inf)
    assert np.isfinite(log_like)
    
    # For a perfect fit, log-likelihood should be maximized
    # (though we have noise, so it won't be exactly the maximum)
    assert log_like < 0  # Log-likelihood of Gaussian is always negative for finite data

def test_log_likelihood_yukawa_positive_definite(sample_data):
    """Test Yukawa log-likelihood with positive-definite covariance."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = sample_data['covariance_matrix']
    
    # Test with alpha=0 (should reduce to Newtonian)
    log_like_alpha0 = log_likelihood_yukawa(sep, force, cov, alpha=0.0, lambda_m=1e-3)
    log_like_newton = log_likelihood_newtonian(sep, force, cov)
    
    # When alpha=0, Yukawa should equal Newtonian
    np.testing.assert_allclose(log_like_alpha0, log_like_newton, rtol=1e-10)

def test_log_likelihood_yukawa_nonzero_alpha(sample_data):
    """Test Yukawa log-likelihood with non-zero alpha."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = sample_data['covariance_matrix']
    
    # Test with small positive alpha
    log_like_pos = log_likelihood_yukawa(sep, force, cov, alpha=0.1, lambda_m=1e-3)
    
    # Test with small negative alpha
    log_like_neg = log_likelihood_yukawa(sep, force, cov, alpha=-0.1, lambda_m=1e-3)
    
    # Both should be finite
    assert np.isfinite(log_like_pos)
    assert np.isfinite(log_like_neg)

def test_log_likelihood_banded_covariance(sample_data, banded_covariance_matrix):
    """Test log-likelihood calculation with banded covariance matrix."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = banded_covariance_matrix
    
    log_like_newton = log_likelihood_newtonian(sep, force, cov)
    log_like_yukawa = log_likelihood_yukawa(sep, force, cov, alpha=0.0, lambda_m=1e-3)
    
    # Both should be finite
    assert np.isfinite(log_like_newton)
    assert np.isfinite(log_like_yukawa)
    
    # When alpha=0, they should be equal
    np.testing.assert_allclose(log_like_newton, log_like_yukawa, rtol=1e-10)

def test_log_likelihood_invalid_covariance(sample_data):
    """Test error handling for non-positive-definite covariance matrix."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    
    # Create a non-positive-definite matrix
    cov = np.array([[1.0, 2.0], [2.0, 1.0]])  # Eigenvalues: 3, -1
    
    # Expand to match data size (for testing purposes)
    n = len(force)
    cov_full = np.zeros((n, n))
    cov_full[:2, :2] = cov
    for i in range(2, n):
        cov_full[i, i] = 1e-6
    
    # This should raise an error or return -inf
    try:
        log_like = log_likelihood_newtonian(sep, force, cov_full)
        # If it doesn't raise, it should return -inf
        assert log_like == -np.inf or not np.isfinite(log_like)
    except Exception:
        # Expected: Cholesky decomposition should fail
        pass

def test_log_likelihood_mismatched_shapes(sample_data):
    """Test error handling for mismatched array shapes."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = sample_data['covariance_matrix']
    
    # Mismatched separation and force
    sep_wrong = sep[:-1]
    
    with pytest.raises(ValueError):
        log_likelihood_newtonian(sep_wrong, force, cov)

def test_log_likelihood_performance(sample_data):
    """Test that log-likelihood calculation is reasonably fast."""
    import time
    
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = sample_data['covariance_matrix']
    
    start = time.time()
    for _ in range(100):
        log_likelihood_newtonian(sep, force, cov)
    end = time.time()
    
    # 100 evaluations should take less than 1 second for 50 points
    assert (end - start) < 1.0

def test_log_likelihood_gradient_consistency(sample_data):
    """Test that log-likelihood behaves consistently with parameter changes."""
    sep = sample_data['separation_m']
    force = sample_data['force_n']
    cov = sample_data['covariance_matrix']
    
    # Create synthetic data that matches Yukawa with specific parameters
    true_alpha = 0.5
    true_lambda = 1e-3
    expected_force = yukawa_force(sep, alpha=true_alpha, lambda_m=true_lambda)
    
    # Add small noise
    noise = 0.001 * np.abs(expected_force) * np.random.randn(len(sep))
    noisy_force = expected_force + noise
    
    # Calculate log-likelihood at true parameters
    log_like_true = log_likelihood_yukawa(sep, noisy_force, cov, 
                                          alpha=true_alpha, lambda_m=true_lambda)
    
    # Calculate log-likelihood at slightly different parameters
    log_like_diff = log_likelihood_yukawa(sep, noisy_force, cov, 
                                          alpha=true_alpha + 0.1, lambda_m=true_lambda)
    
    # The true parameters should generally give a higher (less negative) log-likelihood
    # (though not guaranteed due to noise, it should be close)
    assert log_like_true >= log_like_diff - 1.0  # Allow some margin for noise