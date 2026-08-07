"""
Unit tests for the log-likelihood implementation.

These tests verify:
1. Cholesky decomposition works correctly
2. Log-likelihood is computed correctly for Yukawa and Newtonian models
3. Likelihood returns -inf for invalid parameters
4. Numerical stability with large covariance matrices
"""
import numpy as np
import pytest
from pathlib import Path
import tempfile
import json

from models.likelihood import (
    load_covariance_matrix,
    compute_cholesky_decomposition,
    log_likelihood_yukawa,
    log_likelihood_newtonian,
    YukawaLikelihood,
    NewtonianLikelihood
)
from models.physics import yukawa_force, newtonian_force

@pytest.fixture
def mock_covariance_matrix():
    """Create a mock positive-definite covariance matrix."""
    # Create a simple diagonal covariance matrix
    n = 100
    cov = np.eye(n) * 0.01  # Small variance
    # Add some off-diagonal elements to make it non-trivial
    for i in range(n):
        for j in range(i+1, min(i+5, n)):
            cov[i, j] = 0.005
            cov[j, i] = 0.005
    return cov

@pytest.fixture
def mock_dataset():
    """Create mock dataset for testing."""
    n = 100
    r = np.logspace(-4, -2, n)  # Separation from 0.1mm to 10mm
    f_obs = newtonian_force(r, 6.674e-11) + np.random.normal(0, 0.01, n)
    return r, f_obs

@pytest.fixture
def temp_cov_file(mock_covariance_matrix):
    """Create a temporary covariance matrix file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cov_path = Path(tmpdir) / "covariance_matrix.npy"
        np.save(cov_path, mock_covariance_matrix)
        
        # Create data/processed directory structure
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Move the file to the expected location
        expected_path = Path("data/processed/covariance_matrix.npy")
        if expected_path.exists():
            expected_path.unlink()
        np.save(expected_path, mock_covariance_matrix)
        
        yield expected_path
        
        # Cleanup
        if expected_path.exists():
            expected_path.unlink()

def test_load_covariance_matrix(temp_cov_file):
    """Test loading of covariance matrix."""
    cov = load_covariance_matrix()
    assert cov.shape == (100, 100)
    assert np.allclose(cov, np.load(temp_cov_file))

def test_cholesky_decomposition(temp_cov_file):
    """Test Cholesky decomposition."""
    cov = load_covariance_matrix()
    L, L_inv = compute_cholesky_decomposition(cov)
    
    # Verify L is lower triangular
    assert np.allclose(L, np.tril(L))
    
    # Verify L @ L.T = C
    assert np.allclose(L @ L.T, cov, rtol=1e-10)
    
    # Verify L_inv @ L = I
    assert np.allclose(L_inv @ L, np.eye(L.shape[0]), rtol=1e-10)

def test_log_likelihood_yukawa_positive_params(temp_cov_file, mock_dataset):
    """Test Yukawa log-likelihood with valid parameters."""
    r, f_obs = mock_dataset
    cov = load_covariance_matrix()
    L, L_inv = compute_cholesky_decomposition(cov)
    log_det_cov = 2 * np.sum(np.log(np.diag(L)))
    
    params = (1.0, 1e-4)  # alpha=1, lambda=100 micrometers
    log_l = log_likelihood_yukawa(params, r, f_obs, L_inv, log_det_cov)
    
    # Should return a finite value
    assert np.isfinite(log_l)
    assert log_l < 0  # Log-likelihood should be negative

def test_log_likelihood_yukawa_invalid_lambda(temp_cov_file, mock_dataset):
    """Test Yukawa log-likelihood with invalid lambda."""
    r, f_obs = mock_dataset
    cov = load_covariance_matrix()
    L, L_inv = compute_cholesky_decomposition(cov)
    log_det_cov = 2 * np.sum(np.log(np.diag(L)))
    
    params = (1.0, -1e-4)  # Negative lambda should return -inf
    log_l = log_likelihood_yukawa(params, r, f_obs, L_inv, log_det_cov)
    
    assert log_l == -np.inf

def test_log_likelihood_newtonian(temp_cov_file, mock_dataset):
    """Test Newtonian log-likelihood."""
    r, f_obs = mock_dataset
    cov = load_covariance_matrix()
    L, L_inv = compute_cholesky_decomposition(cov)
    log_det_cov = 2 * np.sum(np.log(np.diag(L)))
    
    params = (6.674e-11,)  # Standard G
    log_l = log_likelihood_newtonian(params, r, f_obs, L_inv, log_det_cov)
    
    assert np.isfinite(log_l)

def test_yukawa_likelihood_class(temp_cov_file, mock_dataset):
    """Test YukawaLikelihood callable class."""
    r, f_obs = mock_dataset
    likelihood = YukawaLikelihood(r, f_obs)
    
    params = (1.0, 1e-4)
    log_l = likelihood(params)
    
    assert np.isfinite(log_l)
    assert likelihood.L_inv is not None
    assert likelihood.log_det_cov is not None

def test_newtonian_likelihood_class(temp_cov_file, mock_dataset):
    """Test NewtonianLikelihood callable class."""
    r, f_obs = mock_dataset
    likelihood = NewtonianLikelihood(r, f_obs)
    
    params = (6.674e-11,)
    log_l = likelihood(params)
    
    assert np.isfinite(log_l)
    assert likelihood.L_inv is not None
    assert likelihood.log_det_cov is not None

def test_likelihood_numerical_stability(temp_cov_file, mock_dataset):
    """Test that likelihood is numerically stable."""
    r, f_obs = mock_dataset
    likelihood = YukawaLikelihood(r, f_obs)
    
    # Test with various parameter combinations
    test_params = [
        (1.0, 1e-4),
        (0.5, 1e-5),
        (2.0, 1e-3),
        (0.1, 1e-6)
    ]
    
    for params in test_params:
        log_l = likelihood(params)
        assert np.isfinite(log_l), f"Likelihood failed for params: {params}"

def test_log_likelihood_consistency(temp_cov_file, mock_dataset):
    """Test that log-likelihood is consistent with manual calculation."""
    r, f_obs = mock_dataset
    cov = load_covariance_matrix()
    L, L_inv = compute_cholesky_decomposition(cov)
    log_det_cov = 2 * np.sum(np.log(np.diag(L)))
    
    params = (1.0, 1e-4)
    alpha, lambda_m = params
    
    # Manual calculation
    f_model = yukawa_force(r, alpha, lambda_m)
    residuals = f_obs - f_model
    whitened_residuals = L_inv @ residuals
    chi_sq = np.sum(whitened_residuals ** 2)
    n = len(f_obs)
    expected_log_l = -0.5 * (n * np.log(2 * np.pi) + log_det_cov + chi_sq)
    
    # Compare with function result
    actual_log_l = log_likelihood_yukawa(params, r, f_obs, L_inv, log_det_cov)
    
    assert np.isclose(actual_log_l, expected_log_l, rtol=1e-10)

def test_missing_covariance_matrix():
    """Test that appropriate error is raised when covariance matrix is missing."""
    # Temporarily move the file
    cov_path = Path("data/processed/covariance_matrix.npy")
    backup_path = Path("data/processed/covariance_matrix.npy.bak")
    
    if cov_path.exists():
        cov_path.rename(backup_path)
    
    try:
        with pytest.raises(FileNotFoundError):
            load_covariance_matrix()
    finally:
        # Restore the file
        if backup_path.exists():
            backup_path.rename(cov_path)

def test_non_positive_definite_matrix():
    """Test behavior with non-positive definite matrix."""
    # Create a non-positive definite matrix
    n = 10
    cov = np.ones((n, n)) * -1  # Negative definite
    
    with pytest.raises(np.linalg.LinAlgError):
        compute_cholesky_decomposition(cov)