"""
Unit tests for Wigner matrix generation.
Verifies statistical properties (mean, variance) and spectral bounds.
"""
import numpy as np
import pytest
from code.generators.wigner import generate_wigner_matrix

def test_wigner_shape():
    """Verify the generated matrix is square."""
    N = 100
    W = generate_wigner_matrix(N)
    assert W.shape == (N, N)

def test_wigner_symmetric():
    """Verify the generated matrix is symmetric."""
    N = 100
    W = generate_wigner_matrix(N)
    assert np.allclose(W, W.T)

def test_wigner_scale():
    """
    Verify spectral bounds for large N.
    According to the Wigner semicircle law, eigenvalues should be within [-2, 2].
    """
    N = 1000
    W = generate_wigner_matrix(N)
    evals = np.linalg.eigvalsh(W)
    # Check max eigenvalue is close to 2.0 (allowing small statistical fluctuation)
    assert np.max(evals) < 2.5
    assert np.min(evals) > -2.5

def test_wigner_mean_variance():
    """
    Verify that off-diagonal entries have mean ~0 and variance ~1/N.
    Diagonal entries have mean ~0 and variance ~2/N (for real symmetric Wigner matrices).
    """
    N = 1000
    W = generate_wigner_matrix(N)
    
    # Extract off-diagonal elements (upper triangle)
    off_diag = W[np.triu_indices(N, k=1)]
    
    # Mean should be close to 0
    assert np.abs(np.mean(off_diag)) < 0.05
    
    # Variance should be close to 1/N
    expected_var = 1.0 / N
    actual_var = np.var(off_diag)
    assert np.abs(actual_var - expected_var) < 0.05 * expected_var

def test_wigner_diagonal_variance():
    """
    Verify diagonal entries have variance ~2/N (standard for Gaussian Orthogonal Ensemble).
    """
    N = 1000
    W = generate_wigner_matrix(N)
    diag = np.diag(W)
    
    expected_var = 2.0 / N
    actual_var = np.var(diag)
    # Allow 10% tolerance for statistical fluctuation
    assert np.abs(actual_var - expected_var) < 0.1 * expected_var