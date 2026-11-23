"""
Unit tests for tokenizer utilities in T015.

Tests error handling for [UNK] tokens in WiC dataset processing.
"""
import torch
import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.tokenizer_utils import (
    handle_unk_tokens,
    get_unk_positions,
    create_context_embedding
)


class TestHandleUnkTokens:
    """Tests for handle_unk_tokens function."""

    def test_no_unk_tokens(self):
        """Test that input without [UNK] tokens is returned unchanged."""
        token_ids = torch.tensor([101, 2023, 2003, 102])
        result = handle_unk_tokens(token_ids)
        assert torch.equal(result, token_ids)

    def test_single_unk_with_context(self):
        """Test [UNK] replacement with available context."""
        # Create input with one [UNK] token (ID 101) surrounded by context
        token_ids = torch.tensor([101, 2023, 101, 2003, 102])  # 101 is [UNK]
        result = handle_unk_tokens(token_ids, unk_token_id=101, context_window=1)
        
        # The [UNK] at index 2 should be replaced with average of neighbors (2023, 2003)
        expected_avg = int(np.mean([2023, 2003]))
        assert result[2] == expected_avg

    def test_multiple_unk_tokens(self):
        """Test handling of multiple [UNK] tokens in sequence."""
        token_ids = torch.tensor([101, 101, 101, 2003, 102])
        result = handle_unk_tokens(token_ids, unk_token_id=101, context_window=1)
        
        # Should not crash and should return valid output shape
        assert result.shape == token_ids.shape
        # First two [UNK]s have limited context, last one has context
        assert result[0] != 101 or result[1] != 101 or result[2] != 101

    def test_batch_input(self):
        """Test handling of batched inputs."""
        token_ids = torch.tensor([
            [101, 2023, 101, 102],
            [101, 101, 2003, 102]
        ])
        result = handle_unk_tokens(token_ids, unk_token_id=101, context_window=1)
        
        assert result.shape == token_ids.shape
        assert result.dim() == 2

    def test_unk_at_boundaries(self):
        """Test [UNK] tokens at sequence boundaries."""
        # [UNK] at start
        token_ids_start = torch.tensor([101, 2023, 2003, 102])
        result_start = handle_unk_tokens(token_ids_start, unk_token_id=101, context_window=2)
        assert result_start.shape == token_ids_start.shape

        # [UNK] at end
        token_ids_end = torch.tensor([101, 2023, 2003, 101])
        result_end = handle_unk_tokens(token_ids_end, unk_token_id=101, context_window=2)
        assert result_end.shape == token_ids_end.shape

    def test_1d_input(self):
        """Test handling of 1D input tensors."""
        token_ids = torch.tensor([101, 2023, 101, 2003, 102])
        result = handle_unk_tokens(token_ids, unk_token_id=101, context_window=1)
        
        assert result.dim() == 1
        assert result.shape[0] == token_ids.shape[0]

    def test_no_context_available(self):
        """Test behavior when no context is available for [UNK]."""
        # Single token sequence that is [UNK]
        token_ids = torch.tensor([101])
        result = handle_unk_tokens(token_ids, unk_token_id=101, context_window=1)
        
        # Should not crash, output shape should match input
        assert result.shape == token_ids.shape


class TestGetUnkPositions:
    """Tests for get_unk_positions function."""

    def test_no_unk_positions(self):
        """Test when there are no [UNK] tokens."""
        token_ids = torch.tensor([101, 2023, 2003, 102])
        positions = get_unk_positions(token_ids, unk_token_id=101)
        assert positions == []

    def test_single_unk_position(self):
        """Test with one [UNK] token."""
        token_ids = torch.tensor([101, 2023, 101, 2003, 102])
        positions = get_unk_positions(token_ids, unk_token_id=101)
        assert len(positions) == 1
        assert positions[0] == (0, 2)

    def test_multiple_unk_positions(self):
        """Test with multiple [UNK] tokens."""
        token_ids = torch.tensor([
            [101, 2023, 101, 102],
            [101, 101, 2003, 102]
        ])
        positions = get_unk_positions(token_ids, unk_token_id=101)
        assert len(positions) == 4
        expected = [(0, 0), (0, 2), (1, 0), (1, 1)]
        assert sorted(positions) == sorted(expected)

    def test_1d_input(self):
        """Test with 1D input."""
        token_ids = torch.tensor([101, 2023, 101])
        positions = get_unk_positions(token_ids, unk_token_id=101)
        assert len(positions) == 2
        assert positions[0] == (0, 0)
        assert positions[1] == (0, 2)


class TestCreateContextEmbedding:
    """Tests for create_context_embedding function."""

    def test_uniform_weights(self):
        """Test context embedding with uniform weights."""
        context_embeddings = torch.tensor([
            [1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0],
            [5.0, 6.0, 7.0]
        ])
        result = create_context_embedding(context_embeddings)
        
        expected = torch.tensor([3.0, 4.0, 5.0])  # Simple average
        assert torch.allclose(result, expected)

    def test_custom_weights(self):
        """Test context embedding with custom weights."""
        context_embeddings = torch.tensor([
            [1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0],
            [5.0, 6.0, 7.0]
        ])
        weights = torch.tensor([0.1, 0.2, 0.7])
        result = create_context_embedding(context_embeddings, weights=weights)
        
        # Weighted average: 0.1*[1,2,3] + 0.2*[3,4,5] + 0.7*[5,6,7]
        expected = torch.tensor([4.2, 5.2, 6.2])
        assert torch.allclose(result, expected)

    def test_single_embedding(self):
        """Test with single context embedding."""
        context_embeddings = torch.tensor([[1.0, 2.0, 3.0]])
        result = create_context_embedding(context_embeddings)
        
        expected = torch.tensor([1.0, 2.0, 3.0])
        assert torch.allclose(result, expected)

    def test_device_consistency(self):
        """Test that result is on the same device as input."""
        context_embeddings = torch.tensor([
            [1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0]
        ])
        result = create_context_embedding(context_embeddings)
        
        assert result.device == context_embeddings.device


if __name__ == "__main__":
    pytest.main([__file__, "-v"])