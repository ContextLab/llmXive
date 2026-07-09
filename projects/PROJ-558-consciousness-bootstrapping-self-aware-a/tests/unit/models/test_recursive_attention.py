"""
Unit tests for recursive_llama.py
"""
import pytest
import torch
from transformers import LlamaConfig

from models.recursive_llama import TemporalRecursiveSelfAttention, RecursionState, RecursiveLlamaWrapper


class TestTemporalRecursiveSelfAttention:
    """Tests for the TemporalRecursiveSelfAttention module."""

    @pytest.fixture
    def config(self):
        """Create a minimal LlamaConfig for testing."""
        return LlamaConfig(
            hidden_size=64,
            num_attention_heads=4,
            num_hidden_layers=1,
            vocab_size=1000,
            max_position_embeddings=128
        )

    @pytest.fixture
    def attention_module(self, config):
        """Create an instance of TemporalRecursiveSelfAttention."""
        return TemporalRecursiveSelfAttention(config)

    @pytest.fixture
    def dummy_hidden_states(self):
        """Create dummy hidden states."""
        return torch.randn(2, 10, 64)  # Batch=2, Seq=10, Hidden=64

    @pytest.fixture
    def dummy_attention_mask(self):
        """Create dummy attention mask."""
        return torch.ones(2, 10)

    def test_shape_consistency(self, attention_module, dummy_hidden_states, dummy_attention_mask):
        """
        Test that output shape matches input shape when no recursion state is provided.
        FR-001: The module must not alter the shape of the input hidden states.
        """
        output, new_state = attention_module(
            hidden_states=dummy_hidden_states,
            attention_mask=dummy_attention_mask,
            recursion_state=None
        )

        assert output.shape == dummy_hidden_states.shape, \
            f"Output shape {output.shape} does not match input shape {dummy_hidden_states.shape}"
        assert new_state is None, "New state should be None when no recursion state is provided"

    def test_attention_mask_propagation(self, attention_module, dummy_hidden_states, dummy_attention_mask):
        """
        Test that attention mask is handled correctly during recursion.
        FR-001: The module must propagate attention masks to ensure correct masking.
        """
        # Create an initial recursion state
        initial_state = RecursionState(
            hidden_states=torch.randn(2, 5, 64), # Previous hidden states
            attention_mask=torch.ones(2, 5),
            depth=0,
            max_depth=2
        )

        output, new_state = attention_module(
            hidden_states=dummy_hidden_states,
            attention_mask=dummy_attention_mask,
            recursion_state=initial_state
        )

        assert new_state is not None, "New state should be created when recursion is active"
        assert new_state.attention_mask is not None, "Attention mask should be propagated"
        # The new mask should be longer (current + previous)
        expected_len = dummy_attention_mask.shape[1] + initial_state.attention_mask.shape[1]
        assert new_state.attention_mask.shape[1] == expected_len, \
            f"Mask length {new_state.attention_mask.shape[1]} != expected {expected_len}"

    def test_recursion_depth_increment(self, attention_module, dummy_hidden_states, dummy_attention_mask):
        """
        Test that recursion depth is correctly incremented.
        """
        initial_state = RecursionState(
            hidden_states=torch.randn(2, 5, 64),
            attention_mask=torch.ones(2, 5),
            depth=1,
            max_depth=3
        )

        _, new_state = attention_module(
            hidden_states=dummy_hidden_states,
            attention_mask=dummy_attention_mask,
            recursion_state=initial_state
        )

        assert new_state.depth == 2, f"Expected depth 2, got {new_state.depth}"
        assert new_state.max_depth == 3, "Max depth should remain unchanged"

    def test_max_depth_termination(self, attention_module, dummy_hidden_states, dummy_attention_mask):
        """
        Test that recursion stops when max depth is reached.
        """
        initial_state = RecursionState(
            hidden_states=torch.randn(2, 5, 64),
            attention_mask=torch.ones(2, 5),
            depth=2, # Already at max depth
            max_depth=2
        )

        output, new_state = attention_module(
            hidden_states=dummy_hidden_states,
            attention_mask=dummy_attention_mask,
            recursion_state=initial_state
        )

        assert new_state is None, "Recursion should stop at max depth"
        # Output should be the same as input when recursion stops
        assert torch.allclose(output, dummy_hidden_states), "Output should match input when recursion stops"


class TestRecursiveLlamaWrapper:
    """Tests for the RecursiveLlamaWrapper class."""

    @pytest.fixture
    def config(self):
        """Create a minimal LlamaConfig for testing."""
        return LlamaConfig(
            hidden_size=64,
            num_attention_heads=4,
            num_hidden_layers=1,
            vocab_size=1000,
            max_position_embeddings=128
        )

    @pytest.fixture
    def wrapper(self, config):
        """Create a RecursiveLlamaWrapper instance."""
        from models.recursive_llama import RecursiveLlamaWrapper
        return RecursiveLlamaWrapper(None, max_recursion_depth=2) # Model is mocked

    def test_wrapper_initialization(self, config):
        """Test that the wrapper initializes correctly."""
        from models.recursive_llama import RecursiveLlamaWrapper
        wrapper = RecursiveLlamaWrapper(None, max_recursion_depth=2)
        assert wrapper.max_recursion_depth == 2
        assert wrapper.recursive_attention is not None

    def test_recursion_depth_limit(self):
        """Test that recursion depth > 2 raises an error."""
        from models.recursive_llama import RecursiveLlamaWrapper
        from models.recursive_llama import RecursionDepthError

        # Create a wrapper with invalid depth
        wrapper = RecursiveLlamaWrapper(None, max_recursion_depth=3)

        # Mock input
        input_ids = torch.randint(0, 1000, (2, 10))

        with pytest.raises(RecursionDepthError):
            wrapper.forward(input_ids=input_ids, recursion_enabled=True)