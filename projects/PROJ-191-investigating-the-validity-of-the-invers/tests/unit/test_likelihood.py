import numpy as np
import pytest
from pathlib import Path
from scipy.linalg import cholesky

from models.likelihood import (
    load_covariance_matrix,
    compute_cholesky_decomposition,
    log_likelihood_newtonian,
    log_likelihood_yukawa
)
from models.physics import newtonian_force, yukawa_force

@pytest.fixture
def dummy_covariance_matrix():
    """Create a simple positive-definite covariance matrix for testing."""
    N = 5
    # Create a random positive-definite matrix
    A = np.random.rand(N, N)
    cov = np.dot(A, A.T)
    return cov

@pytest.fixture
def dummy_data():
    """Create dummy data for testing."""
    N = 5
    separation_m = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    force_n = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    return separation_m, force_n

@pytest.fixture
def cholesky_components(dummy_covariance_matrix):
    """Compute Cholesky components for testing."""
    L, L_inv = compute_cholesky_decomposition(dummy_covariance_matrix)
    log_det = 2 * np.sum(np.log(np.diag(L)))
    return L, L_inv, log_det

def test_load_covariance_matrix(dummy_covariance_matrix, tmp_path):
    """Test loading a covariance matrix from a file."""
    # Save the matrix to a temporary file
    cov_path = tmp_path / "test_cov.npy"
    np.save(cov_path, dummy_covariance_matrix)
    
    # Load it back
    loaded_cov = load_covariance_matrix(cov_path)
    
    # Check that it matches
    np.testing.assert_array_almost_equal(loaded_cov, dummy_covariance_matrix)

def test_load_covariance_matrix_file_not_found():
    """Test that FileNotFoundError is raised when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_covariance_matrix(Path("nonexistent.npy"))

def test_load_covariance_matrix_invalid_shape(tmp_path):
    """Test that ValueError is raised for non-2D array."""
    cov_path = tmp_path / "test_cov.npy"
    np.save(cov_path, np.array([1, 2, 3]))  # 1D array
    
    with pytest.raises(ValueError):
        load_covariance_matrix(cov_path)

def test_compute_cholesky_decomposition(dummy_covariance_matrix):
    """Test Cholesky decomposition computation."""
    L, L_inv = compute_cholesky_decomposition(dummy_covariance_matrix)
    
    # Check that L is lower triangular
    assert np.allclose(L, np.tril(L))
    
    # Check that L @ L.T = cov
    np.testing.assert_array_almost_equal(L @ L.T, dummy_covariance_matrix)
    
    # Check that L_inv is the inverse of L
    np.testing.assert_array_almost_equal(L_inv @ L, np.eye(L.shape[0]))

def test_compute_cholesky_decomposition_not_positive_definite():
    """Test that LinAlgError is raised for non-positive-definite matrix."""
    # Create a non-positive-definite matrix
    cov = np.array([[1, 2], [2, 1]])  # Eigenvalues are 3 and -1
    
    with pytest.raises(np.linalg.LinAlgError):
        compute_cholesky_decomposition(cov)

def test_log_likelihood_newtonian(cholesky_components, dummy_data):
    """Test Newtonian log-likelihood computation."""
    L, L_inv, log_det = cholesky_components
    separation_m, force_n = dummy_data
    
    # Use a dummy parameter
    params = (1.0,)
    
    # Compute log-likelihood
    log_lik = log_likelihood_newtonian(params, separation_m, force_n, L_inv, log_det)
    
    # Check that it's a float
    assert isinstance(log_lik, float)
    
    # Check that it's finite
    assert np.isfinite(log_lik)

def test_log_likelihood_yukawa(cholesky_components, dummy_data):
    """Test Yukawa log-likelihood computation."""
    L, L_inv, log_det = cholesky_components
    separation_m, force_n = dummy_data
    
    # Use dummy parameters
    params = (1.0, 0.1, 0.1)
    
    # Compute log-likelihood
    log_lik = log_likelihood_yukawa(params, separation_m, force_n, L_inv, log_det)
    
    # Check that it's a float
    assert isinstance(log_lik, float)
    
    # Check that it's finite
    assert np.isfinite(log_lik)

def test_log_likelihood_with_identity_covariance(dummy_data):
    """Test log-likelihood with identity covariance matrix."""
    separation_m, force_n = dummy_data
    N = len(force_n)
    
    # Identity covariance matrix
    cov = np.eye(N)
    L, L_inv = compute_cholesky_decomposition(cov)
    log_det = 2 * np.sum(np.log(np.diag(L)))
    
    # For identity covariance, log_det = 0
    assert np.isclose(log_det, 0)
    
    # Use dummy parameters
    params_newtonian = (1.0,)
    log_lik_newtonian = log_likelihood_newtonian(params_newtonian, separation_m, force_n, L_inv, log_det)
    
    # The log-likelihood should be:
    # -0.5 * (chi2 + 0 + N * log(2*pi))
    # where chi2 = sum((force_n - model_force)^2)
    
    # Compute model force
    model_force = newtonian_force(separation_m, 1.0)
    residuals = force_n - model_force
    chi2 = np.sum(residuals ** 2)
    
    expected_log_lik = -0.5 * (chi2 + N * np.log(2 * np.pi))
    
    np.testing.assert_almost_equal(log_lik_newtonian, expected_log_lik)