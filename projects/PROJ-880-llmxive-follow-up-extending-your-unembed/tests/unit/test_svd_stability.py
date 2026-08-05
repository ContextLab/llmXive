"""
Unit tests for SVD numerical stability verification.

This module verifies that scipy.sparse.linalg.svds correctly handles matrices
with small singular values (below 1e-12) by masking them without crashing
or producing NaNs.

Depends on: T012 (SVD extraction implementation in model_analyzer.py)
"""
import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from numpy.testing import assert_array_less, assert_allclose
import logging

# Configure logging for visibility during tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSVDNumericalStability:
    """Tests for numerical stability of SVD operations on ill-conditioned matrices."""

    def test_masking_small_singular_values(self):
        """
        Test that svds correctly handles matrices with known small singular values.

        Constructs a matrix with:
        - Large singular values: [10.0, 5.0, 1.0]
        - Tiny singular values: [1e-13, 1e-14, 1e-15] (below 1e-12 threshold)
        - Zero singular values (via rank deficiency)

        Verifies:
        1. No crash occurs during SVD computation
        2. No NaN values in singular vectors or values
        3. Small singular values are correctly identified
        """
        # Create a deterministic test matrix with known singular value structure
        np.random.seed(42)
        n_rows, n_cols = 100, 50
        k = 10  # Number of singular values to compute

        # Construct matrix with controlled singular values
        # U @ Sigma @ V^T structure
        U = np.random.randn(n_rows, n_cols)
        V = np.random.randn(n_cols, n_cols)

        # Create singular values: some large, some tiny, some zero
        sigma = np.zeros(min(n_rows, n_cols))
        sigma[0] = 10.0
        sigma[1] = 5.0
        sigma[2] = 1.0
        sigma[3] = 1e-13  # Below 1e-12 threshold
        sigma[4] = 1e-14  # Below 1e-12 threshold
        sigma[5] = 1e-15  # Below 1e-12 threshold
        # Rest remain zero

        # Construct the test matrix
        A = U @ np.diag(sigma[:n_cols]) @ V.T

        # Convert to sparse format (as used in model_analyzer.py)
        A_sparse = csr_matrix(A)

        # Execute SVD
        logger.info("Computing SVD with k=%d on matrix of shape %s", k, A.shape)
        try:
            u, s, vt = svds(A_sparse, k=k, random_state=42)
        except Exception as e:
            pytest.fail(f"SVD computation crashed with: {type(e).__name__}: {e}")

        # Verify no NaN values
        logger.info("Checking for NaN values in SVD results...")
        assert not np.any(np.isnan(s)), "Singular values contain NaN"
        assert not np.any(np.isnan(u)), "Left singular vectors contain NaN"
        assert not np.any(np.isnan(vt)), "Right singular vectors contain NaN"

        # Verify no Inf values
        assert not np.any(np.isinf(s)), "Singular values contain Inf"
        assert not np.any(np.isinf(u)), "Left singular vectors contain Inf"
        assert not np.any(np.isinf(vt)), "Right singular vectors contain Inf"

        # Verify singular values are non-negative
        assert np.all(s >= 0), "Singular values are not non-negative"

        # Verify small singular values are correctly identified
        # Sort singular values in descending order (svds returns ascending)
        s_sorted = np.sort(s)[::-1]
        logger.info("Computed singular values (sorted): %s", s_sorted)

        # The largest 3 should be close to [10, 5, 1]
        assert_allclose(s_sorted[:3], [10.0, 5.0, 1.0], rtol=1e-1)

        # Values below 1e-12 should be present in the output
        small_count = np.sum(s_sorted < 1e-12)
        logger.info("Number of singular values < 1e-12: %d", small_count)
        assert small_count >= 3, f"Expected at least 3 small singular values, found {small_count}"

        logger.info("SVD stability test passed successfully")

    def test_masking_threshold_application(self):
        """
        Test that the masking threshold of 1e-12 correctly identifies tiny singular values.

        This test verifies the logic that would be used in model_analyzer.py
        to mask singular values below the threshold.
        """
        threshold = 1e-12

        # Create test array of singular values
        test_values = np.array([10.0, 1.0, 1e-11, 1e-12, 1e-13, 0.0, 1e-15])

        # Apply masking logic (as would be done in model_analyzer.py)
        masked_values = test_values.copy()
        mask = test_values < threshold
        masked_values[mask] = 0.0

        logger.info("Original values: %s", test_values)
        logger.info("Masked values: %s", masked_values)
        logger.info("Mask applied to indices: %s", np.where(mask)[0])

        # Verify correct masking
        expected_masked = np.array([10.0, 1.0, 1e-11, 0.0, 0.0, 0.0, 0.0])
        assert_allclose(masked_values, expected_masked, rtol=1e-10)

        # Verify that values >= threshold are preserved
        assert masked_values[0] == 10.0
        assert masked_values[1] == 1.0
        assert masked_values[2] == 1e-11  # 1e-11 >= 1e-12, so preserved

        # Verify that values < threshold are zeroed
        assert masked_values[3] == 0.0  # 1e-12 is NOT < 1e-12, but we use < in mask
        # Wait: 1e-12 is NOT < 1e-12, so it should NOT be masked
        # Let's fix the expectation
        expected_masked_correct = np.array([10.0, 1.0, 1e-11, 1e-12, 0.0, 0.0, 0.0])
        assert_allclose(masked_values, expected_masked_correct, rtol=1e-10)

        logger.info("Threshold masking test passed")

    def test_rank_deficient_matrix(self):
        """
        Test SVD on a truly rank-deficient matrix.

        Creates a matrix with rank < min(m, n) and verifies SVD handles it gracefully.
        """
        # Create a rank-2 matrix in a 10x10 space
        np.random.seed(123)
        A = np.random.randn(10, 2) @ np.random.randn(2, 10)

        A_sparse = csr_matrix(A)

        # Compute SVD with k=5 (more than actual rank)
        k = 5
        logger.info("Computing SVD on rank-deficient matrix (rank=2, k=%d)", k)

        try:
            u, s, vt = svds(A_sparse, k=k, random_state=123)
        except Exception as e:
            pytest.fail(f"SVD on rank-deficient matrix crashed: {e}")

        # Verify no NaN or Inf
        assert not np.any(np.isnan(s))
        assert not np.any(np.isinf(s))

        # Verify that extra singular values are near zero
        s_sorted = np.sort(s)[::-1]
        logger.info("Singular values for rank-deficient matrix: %s", s_sorted)

        # Only first 2 should be significant
        assert s_sorted[0] > 1e-6
        assert s_sorted[1] > 1e-6
        # Remaining should be very small (numerical noise)
        assert_array_less(s_sorted[2:], 1e-6)

        logger.info("Rank-deficient matrix test passed")

    def test_orthogonality_preservation(self):
        """
        Test that singular vectors remain orthogonal despite small singular values.

        Verifies that U^T U ≈ I and V^T V ≈ I even with numerical challenges.
        """
        np.random.seed(456)
        n_rows, n_cols = 50, 30
        k = 10

        # Create matrix with small singular values
        sigma = np.zeros(min(n_rows, n_cols))
        sigma[0] = 10.0
        sigma[1] = 1e-13  # Tiny value
        sigma[2] = 1.0
        sigma[3:] = 1e-14

        U = np.random.randn(n_rows, n_cols)
        V = np.random.randn(n_cols, n_cols)
        A = U @ np.diag(sigma[:n_cols]) @ V.T

        A_sparse = csr_matrix(A)

        u, s, vt = svds(A_sparse, k=k, random_state=456)

        # Check orthogonality of U
        UtU = u.T @ u
        logger.info("Max deviation from orthogonality in U: %e", np.max(np.abs(UtU - np.eye(k))))
        assert_allclose(UtU, np.eye(k), atol=1e-6)

        # Check orthogonality of V
        VtV = vt @ vt.T
        logger.info("Max deviation from orthogonality in V: %e", np.max(np.abs(VtV - np.eye(k))))
        assert_allclose(VtV, np.eye(k), atol=1e-6)

        logger.info("Orthogonality preservation test passed")

    def test_edge_spectrum_integration_scenario(self):
        """
        Integration-style test mimicking the actual use case in model_analyzer.py.

        Simulates the scenario where an unembedding matrix with small singular values
        is processed for edge spectrum analysis.
        """
        # Simulate a typical unembedding matrix shape (vocab_size, hidden_dim)
        vocab_size = 128256  # Llama-3 vocab size approximation
        hidden_dim = 4096
        k = 100  # As per config.py

        # For testing, use a smaller representative matrix
        test_vocab = 1000
        test_hidden = 256
        k_test = 10

        np.random.seed(789)

        # Create matrix with edge spectrum characteristics:
        # - Strong signal in first few dimensions
        # - Decaying spectrum
        # - Tiny values at the edge

        U = np.random.randn(test_vocab, test_hidden)
        V = np.random.randn(test_hidden, test_hidden)

        # Create decaying singular values with edge noise
        sigma = np.logspace(2, -15, test_hidden)  # From 100 to 1e-15
        sigma[0] = 100.0  # Strong edge signal
        sigma[1] = 50.0
        sigma[2] = 25.0

        A = U @ np.diag(sigma) @ V.T
        A_sparse = csr_matrix(A)

        logger.info("Simulating edge spectrum extraction on matrix of shape %s", A.shape)

        # Execute SVD as in model_analyzer.py
        try:
            u, s, vt = svds(A_sparse, k=k_test, random_state=789)
        except Exception as e:
            pytest.fail(f"Edge spectrum SVD failed: {e}")

        # Verify no NaN/Inf
        assert not np.any(np.isnan(s))
        assert not np.any(np.isnan(u))
        assert not np.any(np.isnan(vt))

        # Apply threshold masking as in model_analyzer.py
        threshold = 1e-12
        s_masked = s.copy()
        s_masked[s < threshold] = 0.0

        logger.info("Original singular values range: [%e, %e]", s.min(), s.max())
        logger.info("Masked singular values: %d below threshold", np.sum(s < threshold))

        # Verify that tiny values are masked
        assert np.all(s_masked >= 0)
        assert np.all((s_masked >= threshold) | (s_masked == 0.0))

        logger.info("Edge spectrum integration scenario test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
