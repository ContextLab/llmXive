"""
Unit tests for feature engineering functions.
"""
import numpy as np
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.feature_engineering import (
    compute_pairwise_correlation,
    fisher_z_transform,
    extract_upper_triangular_vector
)

def test_compute_pairwise_correlation_shape():
    """Test that correlation matrix has correct shape."""
    # Create synthetic time series: 100 time points, 5 nodes
    np.random.seed(42)
    ts = np.random.randn(100, 5)
    
    corr = compute_pairwise_correlation(ts)
    
    assert corr.shape == (5, 5)
    # Diagonal should be 1.0
    assert np.allclose(np.diag(corr), 1.0)

def test_compute_pairwise_correlation_symmetry():
    """Test that correlation matrix is symmetric."""
    np.random.seed(42)
    ts = np.random.randn(100, 5)
    
    corr = compute_pairwise_correlation(ts)
    
    assert np.allclose(corr, corr.T)

def test_fisher_z_transform_range():
    """Test that Fisher-z transform produces valid range."""
    # Correlations close to -1 and 1
    r = np.array([-0.99, -0.5, 0.0, 0.5, 0.99])
    z = fisher_z_transform(r)
    
    # Check that output is finite
    assert np.all(np.isfinite(z))
    
    # Check monotonicity (higher r -> higher z)
    assert np.all(np.diff(z) > 0)

def test_fisher_z_transform_inverse():
    """Test approximate inverse of Fisher-z transform."""
    r_original = np.array([-0.9, -0.5, 0.0, 0.5, 0.9])
    z = fisher_z_transform(r_original)
    
    # Inverse: r = (exp(2z) - 1) / (exp(2z) + 1)
    r_recovered = (np.exp(2 * z) - 1) / (np.exp(2 * z) + 1)
    
    assert np.allclose(r_original, r_recovered, atol=1e-4)

def test_extract_upper_triangular_vector_length():
    """Test that extracted vector has correct length."""
    n = 5
    corr = np.eye(n)
    vec = extract_upper_triangular_vector(corr)
    
    expected_len = n * (n - 1) // 2
    assert len(vec) == expected_len

def test_extract_upper_triangular_vector_values():
    """Test that extracted values match upper triangle."""
    n = 4
    corr = np.random.randn(n, n)
    corr = (corr + corr.T) / 2  # Make symmetric
    
    vec = extract_upper_triangular_vector(corr)
    
    # Reconstruct and compare
    i, j = np.triu_indices(n, k=1)
    expected = corr[i, j]
    
    assert np.allclose(vec, expected)