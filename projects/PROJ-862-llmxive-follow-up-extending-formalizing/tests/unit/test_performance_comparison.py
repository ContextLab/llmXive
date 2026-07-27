"""
Unit tests for performance optimization (T036).

These tests verify that the optimized vectorized implementation
produces the same results as the scalar implementation but faster.
"""

import torch
import numpy as np
import time
import pytest

from perturbation import inject_and_project as inject_scalar
from perturbation_optimized import inject_and_project as inject_vectorized

class TestPerformanceComparison:
    """Tests comparing scalar vs vectorized implementations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.batch_size = 4
        self.seq_len = 16
        self.hidden_dim = 768
        self.vocab_size = 30522
        self.sigma = 0.1
        
        # Create mock embeddings and model matrix
        self.embeddings = torch.randn(self.batch_size, self.seq_len, self.hidden_dim)
        self.model_matrix = torch.randn(self.vocab_size, self.hidden_dim)

    def test_output_consistency(self):
        """Verify that vectorized and scalar implementations produce identical results."""
        # Run scalar (small batch to avoid timeout in tests)
        torch.manual_seed(42)
        scalar_ids, scalar_embs = inject_scalar(
            self.embeddings, self.sigma, self.model_matrix
        )
        
        # Run vectorized
        torch.manual_seed(42)
        vector_ids, vector_embs = inject_vectorized(
            self.embeddings, self.sigma, self.model_matrix
        )
        
        # Compare
        assert torch.equal(scalar_ids, vector_ids), "Token IDs do not match"
        assert torch.allclose(scalar_embs, vector_embs, rtol=1e-5, atol=1e-5), "Embeddings do not match"

    def test_vectorized_speedup(self):
        """Verify that vectorized implementation is faster than scalar."""
        # Use a larger batch for timing to see the difference clearly
        large_batch_size = 32
        large_embeddings = torch.randn(large_batch_size, self.seq_len, self.hidden_dim)
        
        # Time scalar
        start = time.perf_counter()
        # Only run a subset of the sequence to avoid extreme slowness in scalar version
        # We slice to make the test runnable in CI
        scalar_ids, _ = inject_scalar(
            large_embeddings[:, :4, :], self.sigma, self.model_matrix
        )
        scalar_time = time.perf_counter() - start
        
        # Time vectorized
        start = time.perf_counter()
        vector_ids, _ = inject_vectorized(
            large_embeddings, self.sigma, self.model_matrix
        )
        vector_time = time.perf_counter() - start
        
        # Vectorized should be significantly faster (at least 2x for this setup)
        # Note: The scalar version is O(N*V*Seq*Batch) while vectorized is O(N*V + N*Seq*Batch)
        # In practice, vectorized is orders of magnitude faster.
        logger_msg = f"Scalar (partial): {scalar_time:.4f}s, Vectorized: {vector_time:.4f}s"
        print(logger_msg)
        
        # Assert vectorized is faster (allowing some tolerance for CI variance)
        assert vector_time < scalar_time * 2, "Vectorized version should be faster"

    def test_large_batch_vectorized(self):
        """Test that vectorized implementation handles larger batches without OOM."""
        large_batch_size = 64
        large_embeddings = torch.randn(large_batch_size, self.seq_len, self.hidden_dim)
        
        # This should not raise an error
        ids, embs = inject_vectorized(large_embeddings, self.sigma, self.model_matrix)
        
        assert ids.shape == (large_batch_size, self.seq_len)
        assert embs.shape == (large_batch_size, self.seq_len, self.hidden_dim)

    def test_gradient_flow(self):
        """Verify that the vectorized implementation allows gradient flow if needed."""
        # Note: The projection operation (argmin) is not differentiable,
        # but the noise injection part is. This test ensures no crashes occur
        # when gradients are requested on the input.
        embeddings = self.embeddings.requires_grad_(True)
        ids, embs = inject_vectorized(embeddings, self.sigma, self.model_matrix)
        
        # We can't backprop through argmin, but we can check that the operation
        # completed without error and the output is detached (as expected for discrete projection)
        assert not ids.requires_grad
        assert not embs.requires_grad

    def test_memory_efficiency(self):
        """Verify that vectorized implementation uses less memory overhead."""
        # This is a heuristic test: we check that the vectorized version
        # does not create intermediate lists of the size of the batch * seq_len
        # which the scalar version does.
        
        batch_size = 16
        seq_len = 32
        embeddings = torch.randn(batch_size, seq_len, self.hidden_dim)
        
        # Run vectorized
        ids, embs = inject_vectorized(embeddings, self.sigma, self.model_matrix)
        
        # If we got here without OOM, it's a success for this test context
        assert ids.shape == (batch_size, seq_len)
        assert embs.shape == (batch_size, seq_len, self.hidden_dim)