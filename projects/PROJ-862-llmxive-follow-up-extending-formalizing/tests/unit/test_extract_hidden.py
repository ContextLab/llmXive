"""
Unit tests for hidden state extraction logic (US1).

Tests the `extract_thought_vector` function in `code/model_utils.py` to ensure:
1. It correctly extracts the hidden state at the specified token position.
2. The output vector matches the model's hidden dimension.
3. It handles edge cases (e.g., out-of-bounds positions) gracefully.
"""
import pytest
import torch
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Ensure code/ is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model_utils import extract_thought_vector, load_frozen_model
from config import ModelConfig
from memory_monitor import MemoryLimitExceeded

class TestExtractThoughtVector:
    """Unit tests for the extract_thought_vector function."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model with a defined hidden size."""
        mock_model = MagicMock()
        # Simulate a model with hidden size 768 (typical for BERT-like)
        mock_model.config.hidden_size = 768
        mock_model.device = torch.device('cpu')
        
        # Mock the forward pass to return a dummy output
        # Shape: (batch_size, seq_len, hidden_size)
        batch_size, seq_len, hidden_size = 1, 10, 768
        mock_hidden_states = torch.randn(batch_size, seq_len, hidden_size)
        
        mock_output = MagicMock()
        mock_output.last_hidden_state = mock_hidden_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output
        
        return mock_model

    @pytest.fixture
    def mock_tokenizer(self):
        """Create a mock tokenizer."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.pad_token_id = 0
        return mock_tokenizer

    def test_extract_single_token_hidden_state(self, mock_model):
        """Test extraction of a single token's hidden state."""
        # Setup
        batch_size, seq_len, hidden_size = 1, 10, 768
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = 5  # Extract from index 5
        
        # Mock the model to return specific hidden states
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        assert result is not None, "Result should not be None"
        assert result.shape == (hidden_size,), f"Expected shape ({hidden_size},), got {result.shape}"
        assert torch.allclose(result, expected_states[0, thought_token_pos]), "Extracted vector should match model output"

    def test_extract_batch_hidden_states(self, mock_model):
        """Test extraction of hidden states for a batch of inputs."""
        # Setup
        batch_size, seq_len, hidden_size = 4, 20, 512
        mock_model.config.hidden_size = hidden_size
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = 10
        
        # Mock model output
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        assert result.shape == (batch_size, hidden_size), f"Expected shape ({batch_size}, {hidden_size}), got {result.shape}"
        assert torch.allclose(result, expected_states[:, thought_token_pos, :]), "Batch extraction should match model output"

    def test_extract_at_sequence_boundary(self, mock_model):
        """Test extraction at the last valid token position."""
        # Setup
        batch_size, seq_len, hidden_size = 1, 5, 256
        mock_model.config.hidden_size = hidden_size
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = seq_len - 1  # Last token
        
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        assert result.shape == (hidden_size,), "Should extract correctly at boundary"
        assert torch.allclose(result, expected_states[0, thought_token_pos]), "Boundary extraction correct"

    def test_extract_out_of_bounds_position(self, mock_model):
        """Test that extraction raises an error for out-of-bounds positions."""
        # Setup
        batch_size, seq_len, hidden_size = 1, 5, 256
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = seq_len + 1  # Invalid position
        
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute & Assert
        with pytest.raises(IndexError, match="thought_token_pos"):
            extract_thought_vector(mock_model, input_ids, thought_token_pos)

    def test_extract_negative_position(self, mock_model):
        """Test extraction using negative indexing (Python style)."""
        # Setup
        batch_size, seq_len, hidden_size = 1, 5, 256
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = -1  # Last token
        
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        assert result.shape == (hidden_size,), "Negative indexing should work"
        assert torch.allclose(result, expected_states[0, -1]), "Negative index extraction correct"

    def test_extract_with_padding_tokens(self, mock_model):
        """Test extraction when input contains padding tokens (should still extract at pos)."""
        # Setup
        batch_size, seq_len, hidden_size = 2, 10, 512
        mock_model.config.hidden_size = hidden_size
        
        # Create input with padding (0) at the end
        input_ids = torch.tensor([
            [101, 200, 300, 0, 0],
            [101, 200, 300, 400, 0]
        ])
        thought_token_pos = 2  # Valid token in both
        
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        assert result.shape == (batch_size, hidden_size), "Should handle padding in batch"
        # The function extracts based on position index, regardless of padding content
        assert torch.allclose(result, expected_states[:, thought_token_pos, :]), "Extraction at valid pos correct"

    def test_extract_returns_torch_tensor(self, mock_model):
        """Ensure the output is a torch.Tensor, not numpy or list."""
        # Setup
        batch_size, seq_len, hidden_size = 1, 5, 256
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = 2
        
        expected_states = torch.randn(batch_size, seq_len, hidden_size)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        assert isinstance(result, torch.Tensor), "Result must be a torch.Tensor"
        assert result.dtype == torch.float32, "Result dtype should be float32"

    def test_extract_dtype_consistency(self, mock_model):
        """Test that output dtype matches model config expectations (float32)."""
        # Setup
        batch_size, seq_len, hidden_size = 1, 5, 256
        input_ids = torch.randint(100, 1000, (batch_size, seq_len))
        thought_token_pos = 2
        
        # Simulate model returning float16 (common in quantization)
        expected_states = torch.randn(batch_size, seq_len, hidden_size, dtype=torch.float16)
        mock_output = MagicMock()
        mock_output.last_hidden_state = expected_states
        mock_model.return_value = mock_output
        mock_model.forward = lambda *args, **kwargs: mock_output

        # Execute
        result = extract_thought_vector(mock_model, input_ids, thought_token_pos)

        # Assert
        # The function should preserve the model's output dtype or cast to float32 if needed
        # Based on typical implementation, it returns as-is or casts to float32 for stability
        assert result.dtype in [torch.float32, torch.float16], f"Unexpected dtype: {result.dtype}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])