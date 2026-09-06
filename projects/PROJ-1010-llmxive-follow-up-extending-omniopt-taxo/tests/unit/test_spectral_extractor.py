"""
Unit tests for numerical stability of eigenvalue decomposition in spectral extraction.

This module verifies that the spectral extraction logic handles:
1. Singular matrices (zero eigenvalues) gracefully
2. Near-singular matrices (ill-conditioned) with regularization
3. Valid positive semi-definite matrices
4. Edge cases with very small or very large values

Tests are designed to run without GPU and with minimal memory footprint.
"""

import numpy as np
import pytest
from typing import Tuple, List
import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.seeds import set_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# Import the function to test - we'll implement a minimal version inline for testing
# In the actual implementation, this would be in code/spectral_extractor.py
def compute_eigenvalues_stable(matrix: np.ndarray, regularization: float = 1e-8) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute eigenvalues and eigenvectors of a symmetric matrix with numerical stability.
    
    This is a minimal implementation for testing purposes. The actual implementation
    in spectral_extractor.py will be more sophisticated.
    
    Args:
        matrix: Symmetric matrix (n x n)
        regularization: Small value added to diagonal for stability
        
    Returns:
        Tuple of (eigenvalues, eigenvectors)
        
    Raises:
        ValueError: If matrix is not square or symmetric
        RuntimeError: If eigenvalue decomposition fails
    """
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be square")
    
    # Check symmetry
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise ValueError("Matrix must be symmetric")
    
    # Add regularization for numerical stability
    reg_matrix = matrix + regularization * np.eye(matrix.shape[0])
    
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(reg_matrix)
        
        # Sort in descending order
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        return eigenvalues, eigenvectors
        
    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"Eigenvalue decomposition failed: {e}")

def compute_spectral_features(eigenvalues: np.ndarray) -> dict:
    """
    Compute spectral features from eigenvalues.
    
    Args:
        eigenvalues: Array of eigenvalues (sorted descending)
        
    Returns:
        Dictionary with spectral features
    """
    if len(eigenvalues) == 0:
        raise ValueError("Eigenvalues array cannot be empty")
    
    # Filter out negative eigenvalues (should be zero for PSD matrices)
    positive_eigenvalues = eigenvalues[eigenvalues > 0]
    
    if len(positive_eigenvalues) == 0:
        # All eigenvalues are zero or negative
        return {
            'spectral_radius': 0.0,
            'condition_number': 1.0,  # By convention for zero matrix
            'tail_decay_exponent': 0.0,
            'spectral_entropy': 0.0
        }
    
    # Spectral radius: largest eigenvalue
    spectral_radius = positive_eigenvalues[0]
    
    # Condition number: ratio of largest to smallest positive eigenvalue
    if len(positive_eigenvalues) > 1:
        condition_number = positive_eigenvalues[0] / positive_eigenvalues[-1]
    else:
        condition_number = 1.0
    
    # Tail decay exponent: fit power law to top 50% of eigenvalues
    if len(positive_eigenvalues) >= 2:
        # Use log-log linear regression
        top_half = positive_eigenvalues[:len(positive_eigenvalues)//2]
        if len(top_half) >= 2 and np.all(top_half > 0):
            x = np.arange(1, len(top_half) + 1)
            y = np.log(top_half)
            x_log = np.log(x)
            
            # Linear regression: y = a + b*x
            coeffs = np.polyfit(x_log, y, 1)
            tail_decay_exponent = -coeffs[0]  # Negative slope
        else:
            tail_decay_exponent = 0.0
    else:
        tail_decay_exponent = 0.0
    
    # Spectral entropy: Shannon entropy of normalized eigenvalue distribution
    normalized = positive_eigenvalues / np.sum(positive_eigenvalues)
    # Avoid log(0)
    normalized = np.clip(normalized, 1e-10, 1.0)
    spectral_entropy = -np.sum(normalized * np.log2(normalized))
    
    return {
        'spectral_radius': spectral_radius,
        'condition_number': condition_number,
        'tail_decay_exponent': tail_decay_exponent,
        'spectral_entropy': spectral_entropy
    }

class TestEigenvalueDecompositionStability:
    """Test suite for numerical stability of eigenvalue decomposition."""
    
    def setup_method(self):
        """Set up test fixtures."""
        set_seed(42)
        self.logger = get_logger(__name__)
    
    def test_perfectly_conditioned_matrix(self):
        """Test with a well-conditioned identity matrix."""
        n = 10
        matrix = np.eye(n)
        
        eigenvalues, eigenvectors = compute_eigenvalues_stable(matrix)
        
        # All eigenvalues should be 1.0 (or very close due to regularization)
        assert np.allclose(eigenvalues, 1.0, atol=1e-6)
        assert len(eigenvalues) == n
        
        features = compute_spectral_features(eigenvalues)
        assert np.isclose(features['spectral_radius'], 1.0, atol=1e-6)
        assert np.isclose(features['condition_number'], 1.0, atol=1e-6)
    
    def test_singular_matrix(self):
        """Test with a singular matrix (rank-deficient)."""
        # Create a rank-5 matrix of size 10x10
        n = 10
        A = np.random.randn(n, 5)
        matrix = A @ A.T  # This is rank 5, so 5 zero eigenvalues
        
        eigenvalues, eigenvectors = compute_eigenvalues_stable(matrix)
        
        # Should not raise an exception
        assert len(eigenvalues) == n
        
        # Check that we have 5 non-zero eigenvalues (approximately)
        non_zero_count = np.sum(eigenvalues > 1e-6)
        assert non_zero_count == 5
        
        # Features should still be computable
        features = compute_spectral_features(eigenvalues)
        assert 'spectral_radius' in features
        assert 'condition_number' in features
        assert features['condition_number'] > 1.0
    
    def test_ill_conditioned_matrix(self):
        """Test with a very ill-conditioned matrix."""
        n = 10
        # Create matrix with eigenvalues ranging from 1 to 1e-10
        eigenvalues_true = np.logspace(0, -10, n)
        Q = np.random.randn(n, n)
        Q, _ = np.linalg.qr(Q)  # Orthogonal matrix
        matrix = Q @ np.diag(eigenvalues_true) @ Q.T
        
        eigenvalues, eigenvectors = compute_eigenvalues_stable(matrix)
        
        # Should not raise an exception
        assert len(eigenvalues) == n
        
        # The smallest eigenvalue might be slightly perturbed due to regularization
        # but should still be very small
        assert eigenvalues[-1] < 1e-8
        
        features = compute_spectral_features(eigenvalues)
        # Condition number should be large but finite
        assert features['condition_number'] > 1e6
        assert np.isfinite(features['condition_number'])
    
    def test_zero_matrix(self):
        """Test with a completely zero matrix."""
        n = 10
        matrix = np.zeros((n, n))
        
        eigenvalues, eigenvectors = compute_eigenvalues_stable(matrix)
        
        # All eigenvalues should be close to zero (regularization adds 1e-8)
        assert np.allclose(eigenvalues, 1e-8, atol=1e-10)
        
        features = compute_spectral_features(eigenvalues)
        assert features['spectral_radius'] < 1e-7
        assert features['condition_number'] == 1.0  # By convention
    
    def test_large_values(self):
        """Test with very large eigenvalues."""
        n = 10
        eigenvalues_true = np.logspace(10, 15, n)
        Q = np.random.randn(n, n)
        Q, _ = np.linalg.qr(Q)
        matrix = Q @ np.diag(eigenvalues_true) @ Q.T
        
        eigenvalues, eigenvectors = compute_eigenvalues_stable(matrix)
        
        assert len(eigenvalues) == n
        assert np.all(eigenvalues > 0)
        
        features = compute_spectral_features(eigenvalues)
        assert np.isfinite(features['spectral_radius'])
        assert np.isfinite(features['condition_number'])
    
    def test_small_values(self):
        """Test with very small eigenvalues."""
        n = 10
        eigenvalues_true = np.logspace(-15, -10, n)
        Q = np.random.randn(n, n)
        Q, _ = np.linalg.qr(Q)
        matrix = Q @ np.diag(eigenvalues_true) @ Q.T
        
        eigenvalues, eigenvectors = compute_eigenvalues_stable(matrix)
        
        assert len(eigenvalues) == n
        assert np.all(eigenvalues > 0)
        
        features = compute_spectral_features(eigenvalues)
        assert np.isfinite(features['spectral_radius'])
        assert np.isfinite(features['condition_number'])
    
    def test_asymmetric_matrix_raises_error(self):
        """Test that asymmetric matrix raises an error."""
        n = 5
        matrix = np.random.randn(n, n)
        # Make it asymmetric
        matrix[0, 1] = 100.0
        matrix[1, 0] = 0.0
        
        with pytest.raises(ValueError, match="Matrix must be symmetric"):
            compute_eigenvalues_stable(matrix)
    
    def test_non_square_matrix_raises_error(self):
        """Test that non-square matrix raises an error."""
        matrix = np.random.randn(5, 3)
        
        with pytest.raises(ValueError, match="Matrix must be square"):
            compute_eigenvalues_stable(matrix)
    
    def test_empty_matrix_raises_error(self):
        """Test that empty matrix raises an error."""
        matrix = np.zeros((0, 0))
        
        with pytest.raises(ValueError, match="Eigenvalues array cannot be empty"):
            compute_spectral_features(np.array([]))
    
    def test_single_eigenvalue(self):
        """Test with a single eigenvalue."""
        eigenvalues = np.array([5.0])
        
        features = compute_spectral_features(eigenvalues)
        
        assert features['spectral_radius'] == 5.0
        assert features['condition_number'] == 1.0
        assert features['spectral_entropy'] == 0.0
        assert features['tail_decay_exponent'] == 0.0
    
    def test_numerical_precision(self):
        """Test that results are numerically stable across different runs."""
        set_seed(42)
        n = 20
        A = np.random.randn(n, n)
        matrix = A @ A.T  # Symmetric positive semi-definite
        
        eigenvalues1, _ = compute_eigenvalues_stable(matrix)
        eigenvalues2, _ = compute_eigenvalues_stable(matrix)
        
        # Results should be identical for the same input
        assert np.allclose(eigenvalues1, eigenvalues2, atol=1e-10)
    
    def test_gradient_covariance_simulation(self):
        """Simulate a gradient covariance matrix scenario."""
        # Simulate gradients from a neural network training step
        batch_size = 64
        num_params = 100
        
        # Simulate gradients with some correlation structure
        gradients = np.random.randn(batch_size, num_params)
        # Add some correlation
        gradients[:, :10] += gradients[:, 0:1] * 0.5
        
        # Compute covariance matrix
        cov_matrix = (gradients.T @ gradients) / batch_size
        
        # This should work without issues
        eigenvalues, eigenvectors = compute_eigenvalues_stable(cov_matrix)
        
        assert len(eigenvalues) == num_params
        assert np.all(eigenvalues >= 0)
        
        features = compute_spectral_features(eigenvalues)
        assert all(np.isfinite(v) for v in features.values())
    
    def test_rank_deficient_gradient_covariance(self):
        """Test with rank-deficient gradient covariance (common in practice)."""
        batch_size = 10
        num_params = 100  # More parameters than samples -> rank deficient
        
        gradients = np.random.randn(batch_size, num_params)
        cov_matrix = (gradients.T @ gradients) / batch_size
        
        # Rank should be at most 10
        eigenvalues, eigenvectors = compute_eigenvalues_stable(cov_matrix)
        
        # Should have at most 10 non-zero eigenvalues
        non_zero_count = np.sum(eigenvalues > 1e-6)
        assert non_zero_count <= batch_size
        
        # Should still compute features without error
        features = compute_spectral_features(eigenvalues)
        assert all(np.isfinite(v) for v in features.values())
    
    def test_tail_decay_computation(self):
        """Test tail decay exponent computation with known power law."""
        # Create eigenvalues following a power law: lambda_i ~ i^(-alpha)
        n = 100
        alpha = 2.0
        eigenvalues = np.arange(1, n + 1) ** (-alpha)
        
        features = compute_spectral_features(eigenvalues)
        
        # The tail decay exponent should be close to alpha
        # (with some approximation error due to discrete sampling)
        assert 1.5 < features['tail_decay_exponent'] < 2.5
    
    def test_spectral_entropy_bounds(self):
        """Test that spectral entropy is within expected bounds."""
        # Maximum entropy: uniform distribution
        n = 10
        uniform_eigenvalues = np.ones(n) / n
        entropy_uniform = compute_spectral_features(uniform_eigenvalues)['spectral_entropy']
        assert np.isclose(entropy_uniform, np.log2(n), atol=0.1)
        
        # Minimum entropy: single dominant eigenvalue
        concentrated_eigenvalues = np.zeros(n)
        concentrated_eigenvalues[0] = 1.0
        entropy_concentrated = compute_spectral_features(concentrated_eigenvalues)['spectral_entropy']
        assert np.isclose(entropy_concentrated, 0.0, atol=1e-6)
        
        # Random eigenvalues should be between these bounds
        random_eigenvalues = np.random.rand(n)
        random_eigenvalues /= np.sum(random_eigenvalues)
        entropy_random = compute_spectral_features(random_eigenvalues)['spectral_entropy']
        assert 0 <= entropy_random <= np.log2(n)