"""
Unit tests for feature engineering functions.
Tests Fisher-z transformation and variance calculations.
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
    extract_upper_triangular_vector,
    process_subject_features
)

class TestFisherZTransform:
    def test_fisher_z_identity(self):
        """Test that Fisher-z of 0 is 0"""
        assert abs(fisher_z_transform(0.0)) < 1e-6

    def test_fisher_z_positive(self):
        """Test Fisher-z for positive correlation"""
        z = fisher_z_transform(0.5)
        assert z > 0
        
    def test_fisher_z_negative(self):
        """Test Fisher-z for negative correlation"""
        z = fisher_z_transform(-0.5)
        assert z < 0

    def test_fisher_z_edge_cases(self):
        """Test Fisher-z handles extreme values without crashing"""
        # Should not raise error, though values will be large
        z_pos = fisher_z_transform(0.9999)
        z_neg = fisher_z_transform(-0.9999)
        assert z_pos > 0
        assert z_neg < 0

class TestCorrelationMatrix:
    def test_symmetric_matrix(self):
        """Test that correlation matrix is symmetric"""
        # Create simple time series: 100 timepoints, 5 regions
        np.random.seed(42)
        ts = np.random.randn(100, 5)
        corr = compute_pairwise_correlation(ts)
        
        # Check symmetry
        assert np.allclose(corr, corr.T)

    def test_diagonal_ones(self):
        """Test that diagonal of correlation matrix is 1"""
        np.random.seed(42)
        ts = np.random.randn(100, 5)
        corr = compute_pairwise_correlation(ts)
        
        # Check diagonal
        assert np.allclose(np.diag(corr), 1.0)

    def test_shape(self):
        """Test output shape matches input regions"""
        np.random.seed(42)
        ts = np.random.randn(100, 10)
        corr = compute_pairwise_correlation(ts)
        assert corr.shape == (10, 10)

class TestUpperTriangularExtraction:
    def test_vector_length(self):
        """Test vector length for n regions is n*(n-1)/2"""
        n = 10
        corr_matrix = np.eye(n)
        vec = extract_upper_triangular_vector(corr_matrix)
        expected_len = n * (n - 1) // 2
        assert len(vec) == expected_len

    def test_excludes_diagonal(self):
        """Test that diagonal elements are excluded"""
        n = 5
        corr_matrix = np.ones((n, n))  # All ones
        vec = extract_upper_triangular_vector(corr_matrix)
        # If diagonal were included, we'd have n^2 elements
        # Excluding diagonal and lower triangle: n*(n-1)/2
        assert len(vec) == n * (n - 1) // 2

class TestProcessSubjectFeatures:
    def test_output_shape(self):
        """Test output vector shape"""
        np.random.seed(42)
        ts = np.random.randn(100, 10)
        vec = process_subject_features(ts)
        
        # 10 regions -> 10*9/2 = 45 edges
        expected_len = 10 * 9 // 2
        assert len(vec) == expected_len

    def test_deterministic(self):
        """Test that processing is deterministic"""
        np.random.seed(42)
        ts = np.random.randn(100, 5)
        
        vec1 = process_subject_features(ts)
        vec2 = process_subject_features(ts)
        
        assert np.allclose(vec1, vec2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])