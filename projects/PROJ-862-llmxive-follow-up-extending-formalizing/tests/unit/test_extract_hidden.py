"""
Unit tests for hidden state extraction logic in code/model_utils.py.

Tests cover:
1. Correct extraction of hidden state at specified token position.
2. Dimensionality validation (output matches model hidden size).
3. Handling of edge cases (padding, multiple layers if applicable).
4. Integration with the frozen model loading (CPU-only).
"""
import pytest
import torch
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function under test
from code.model_utils import load_frozen_model, extract_hidden_state
from code.config import ModelConfig, NoiseSweepConfig, ValidityConfig, MemoryConfig, DataConfig, OutputPaths, PipelineConfig
from code.memory_monitor import MemoryLimitExceeded

# Mock configuration for testing
@pytest.fixture
def mock_model_config():
    return ModelConfig(
        model_name_or_path="hf-internal-testing/tiny-random-LlamaForCausalLM", # Small model for testing
        hidden_size=32, # Tiny model hidden size
        num_hidden_layers=2,
        use_cpu=True
    )

@pytest.fixture
def mock_tokenizer():
    # Using a tiny tokenizer for testing
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained("hf-internal-testing/tiny-random-LlamaForCausalLM")

@pytest.fixture
def mock_model(mock_model_config):
    # Load a real tiny model to ensure the extraction logic works with actual tensors
    model = load_frozen_model(mock_model_config)
    model.eval()
    return model

def test_extract_hidden_state_basic(mock_model, mock_tokenizer, mock_model_config):
    """Test basic extraction of hidden state at a specific token position."""
    text = "The quick brown fox jumps over the lazy dog."
    inputs = mock_tokenizer(text, return_tensors="pt", padding=True)
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    # Extract hidden state for the last token (before padding if any)
    # We'll pick a specific position, e.g., the 3rd token
    token_pos = 3
    
    if token_pos >= input_ids.shape[1]:
        pytest.skip("Token position out of bounds for this input length")
    
    hidden_state = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    
    # Assertions
    assert hidden_state is not None, "Hidden state should not be None"
    assert isinstance(hidden_state, torch.Tensor), "Hidden state should be a torch.Tensor"
    
    # Check dimensionality: should be [batch_size, hidden_size]
    # Since we are extracting for a specific position, the output should be [1, hidden_size]
    expected_shape = (1, mock_model_config.hidden_size)
    assert hidden_state.shape == expected_shape, f"Expected shape {expected_shape}, got {hidden_state.shape}"
    
    # Check for NaN or Inf values
    assert not torch.isnan(hidden_state).any(), "Hidden state should not contain NaN values"
    assert not torch.isinf(hidden_state).any(), "Hidden state should not contain Inf values"

def test_extract_hidden_state_padding_handling(mock_model, mock_tokenizer, mock_model_config):
    """Test extraction when input has padding."""
    text = "Short"
    inputs = mock_tokenizer(text, return_tensors="pt", padding="max_length", max_length=10)
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    # Extract hidden state for a valid token position (not padding)
    token_pos = 1 # First real token after special tokens
    
    hidden_state = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    
    assert hidden_state is not None
    assert hidden_state.shape[0] == 1
    assert hidden_state.shape[1] == mock_model_config.hidden_size

def test_extract_hidden_state_invalid_position(mock_model, mock_tokenizer, mock_model_config):
    """Test extraction with an invalid token position (out of bounds)."""
    text = "Test"
    inputs = mock_tokenizer(text, return_tensors="pt")
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    # Position out of bounds
    token_pos = input_ids.shape[1] + 5
    
    with pytest.raises((IndexError, ValueError)):
        extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)

def test_extract_hidden_state_batch(mock_model, mock_tokenizer, mock_model_config):
    """Test extraction with a batch of inputs."""
    texts = ["First sentence.", "Second sentence."]
    inputs = mock_tokenizer(texts, return_tensors="pt", padding=True)
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    token_pos = 2 # A valid position for both sentences
    
    hidden_states = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    
    # Should return [batch_size, hidden_size]
    assert hidden_states.shape[0] == len(texts)
    assert hidden_states.shape[1] == mock_model_config.hidden_size

def test_extract_hidden_state_with_cpu_only(mock_model, mock_tokenizer, mock_model_config):
    """Ensure extraction works in CPU-only mode."""
    text = "CPU only test."
    inputs = mock_tokenizer(text, return_tensors="pt")
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    token_pos = 1
    
    # Ensure model is on CPU
    assert next(mock_model.parameters()).device.type == "cpu"
    
    hidden_state = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    
    assert hidden_state.device.type == "cpu"
    assert hidden_state.shape == (1, mock_model_config.hidden_size)

def test_extract_hidden_state_numerical_stability(mock_model, mock_tokenizer, mock_model_config):
    """Test that extraction produces numerically stable results."""
    text = "Stability check."
    inputs = mock_tokenizer(text, return_tensors="pt")
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    token_pos = 1
    
    # Run multiple times to check for consistency (no random ops in forward pass for frozen model)
    hidden_state_1 = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    hidden_state_2 = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    
    assert torch.allclose(hidden_state_1, hidden_state_2, atol=1e-6), "Results should be deterministic"

def test_extract_hidden_state_layer_selection(mock_model, mock_tokenizer, mock_model_config):
    """
    Test extraction from a specific layer if the model supports it.
    Note: The current extract_hidden_state implementation might default to last layer.
    This test ensures we can access layer outputs if the function signature is extended.
    For now, it verifies the basic extraction works as expected.
    """
    text = "Layer test."
    inputs = mock_tokenizer(text, return_tensors="pt")
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    token_pos = 1
    
    # This test primarily ensures the function doesn't crash and returns correct shape
    hidden_state = extract_hidden_state(mock_model, input_ids, attention_mask, token_pos)
    
    assert hidden_state.shape == (1, mock_model_config.hidden_size)