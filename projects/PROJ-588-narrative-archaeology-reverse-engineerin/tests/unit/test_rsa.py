"""
Unit tests for RSA dissimilarity matrix calculation (T019).

Tests the `compute_dissimilarity_matrix` function from `code/models/rsa.py`.
Verifies:
1. Correct shape of the output matrix (N x N).
2. Symmetry of the matrix.
3. Zero values on the diagonal (self-similarity).
4. Correct calculation of dissimilarity (1 - correlation) for known inputs.
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.models.rsa import compute_dissimilarity_matrix


class TestComputeDissimilarityMatrix:
    """Tests for the compute_dissimilarity_matrix function."""

    def test_output_shape(self):
        """Test that the output matrix is square (N x N)."""
        n_events = 10
        n_voxels = 5
        # Create dummy timecourses: (n_events, n_voxels)
        # Using random data for shape test
        rng = np.random.default_rng(42)
        timecourses = rng.standard_normal((n_events, n_voxels))

        rdm = compute_dissimilarity_matrix(timecourses)

        assert rdm.shape == (n_events, n_events), \
            f"Expected shape ({n_events}, {n_events}), got {rdm.shape}"

    def test_symmetry(self):
        """Test that the RDM is symmetric (R[i,j] == R[j,i])."""
        rng = np.random.default_rng(42)
        timecourses = rng.standard_normal((8, 6))

        rdm = compute_dissimilarity_matrix(timecourses)

        # Check symmetry within floating point tolerance
        assert np.allclose(rdm, rdm.T), "RDM is not symmetric"

    def test_diagonal_zeros(self):
        """Test that the diagonal elements are zero (self-similarity)."""
        rng = np.random.default_rng(42)
        timecourses = rng.standard_normal((8, 6))

        rdm = compute_dissimilarity_matrix(timecourses)

        # Diagonal should be 0 (1 - correlation(1.0) = 0)
        np.testing.assert_array_almost_equal(
            np.diag(rdm),
            np.zeros(timecourses.shape[0]),
            decimal=5,
            err_msg="Diagonal elements should be zero"
        )

    def test_known_correlation(self):
        """Test calculation with a known correlation case."""
        # Create two identical vectors
        v1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        # Create a second vector perfectly correlated with v1
        v2 = v1 * 2 + 1  # Linear transformation preserves correlation = 1.0
        
        # Create a third vector uncorrelated (or negatively correlated)
        v3 = np.array([5.0, 4.0, 3.0, 2.0, 1.0]) # Perfectly negatively correlated (-1.0)

        # Stack into (n_events, n_features)
        timecourses = np.vstack([v1, v2, v3])

        rdm = compute_dissimilarity_matrix(timecourses)

        # R[0, 1] should be 1 - 1.0 = 0.0
        expected_01 = 0.0
        assert np.isclose(rdm[0, 1], expected_01, atol=1e-5), \
            f"Expected R[0,1] to be {expected_01}, got {rdm[0, 1]}"

        # R[0, 2] should be 1 - (-1.0) = 2.0
        expected_02 = 2.0
        assert np.isclose(rdm[0, 2], expected_02, atol=1e-5), \
            f"Expected R[0,2] to be {expected_02}, got {rdm[0, 2]}"

    def test_single_event(self):
        """Test edge case with a single event."""
        timecourses = np.array([[1.0, 2.0, 3.0]])
        
        rdm = compute_dissimilarity_matrix(timecourses)
        
        assert rdm.shape == (1, 1)
        assert rdm[0, 0] == 0.0

    def test_constant_timecourse_handling(self):
        """Test behavior when a timecourse has zero variance (constant)."""
        # One constant vector, one normal vector
        # Correlation is undefined for constant vectors, usually returns NaN or 0 depending on implementation
        # We expect the function to handle this gracefully (likely producing NaN or a defined fallback)
        # The implementation uses scipy.spatial.distance.pdist with 'correlation', which returns 1.0 for constant vectors 
        # (since correlation is undefined, but distance logic often treats it as max dissimilarity or 0).
        # Let's verify it doesn't crash.
        
        v_const = np.array([1.0, 1.0, 1.0])
        v_var = np.array([1.0, 2.0, 3.0])
        
        timecourses = np.vstack([v_const, v_var])
        
        # This should not raise an exception
        try:
            rdm = compute_dissimilarity_matrix(timecourses)
            # If it runs, it's a pass for this unit test (graceful handling)
            assert rdm.shape == (2, 2)
        except Exception as e:
            pytest.fail(f"compute_dissimilarity_matrix raised an exception on constant timecourse: {e}")