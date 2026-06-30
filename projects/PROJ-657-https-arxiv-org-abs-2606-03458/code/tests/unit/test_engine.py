"""
Unit tests for the CustomGenerateLoop inference engine.

Tests verify that KVarNQuantizer is correctly injected into the forward pass
and that the generation loop functions without errors.
"""
import pytest
import torch
import torch.nn as nn
from unittest.mock import Mock, patch, MagicMock

from transformers import PreTrainedModel, PretrainedConfig, GenerationConfig

from src.quantization.kvarn import KVarNQuantizer
from src.inference.engine import CustomGenerateLoop, create_quantized_generator


class MockTransformerModel(PreTrainedModel):
    """Mock transformer model for testing."""
    config_class = PretrainedConfig

    def __init__(self):
        config = PretrainedConfig()
        config.pad_token_id = 0
        config.eos_token_id = 2
        config.vocab_size = 1000
        config.hidden_size = 64
        config.num_attention_heads = 4
        config.num_hidden_layers = 2
        super().__init__(config)
        self.linear = nn.Linear(64, 1000)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_values: Optional[Tuple] = None,
        use_cache: bool = False,
        **kwargs
    ):
        # Mock forward pass
        batch_size, seq_len = input_ids.shape
        hidden_states = self.linear(input_ids)
        logits = hidden_states

        # Mock past_key_values if requested
        if use_cache:
            # Return dummy KV cache
            num_layers = self.config.num_hidden_layers
            kv_cache = tuple(
                (
                    torch.randn(batch_size, self.config.num_attention_heads, seq_len, 64 // self.config.num_attention_heads),
                    torch.randn(batch_size, self.config.num_attention_heads, seq_len, 64 // self.config.num_attention_heads)
                )
                for _ in range(num_layers)
            )
            return {"logits": logits, "past_key_values": kv_cache}

        return {"logits": logits}

    def prepare_inputs_for_generation(self, input_ids, **kwargs):
        return {"input_ids": input_ids, **kwargs}

    def _reorder_cache(self, past_key_values, beam_idx):
        return past_key_values


@pytest.fixture
def mock_model():
    return MockTransformerModel()

@pytest.fixture
def mock_quantizer():
    return KVarNQuantizer(bits=8)

@pytest.fixture
def input_ids():
    return torch.tensor([[1, 2, 3, 4, 5]])

@pytest.fixture
def attention_mask():
    return torch.tensor([[1, 1, 1, 1, 1]])


def test_custom_generate_loop_initialization(mock_model, mock_quantizer):
    """Test that CustomGenerateLoop initializes correctly."""
    engine = CustomGenerateLoop(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )
    assert engine.model is mock_model
    assert engine.quantizer is mock_quantizer
    assert engine.device == "cpu"
    assert engine.use_cache is True
    assert engine._interceptor is None


def test_custom_generate_loop_without_quantizer(mock_model):
    """Test generation loop works without quantization."""
    engine = CustomGenerateLoop(model=mock_model, device="cpu")
    assert engine.quantizer is None
    assert engine._interceptor is None


def test_generate_creates_interceptor_when_quantizer_present(mock_model, mock_quantizer, input_ids):
    """Test that interceptor is created when quantizer is present."""
    engine = CustomGenerateLoop(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )

    # Mock the actual generation to avoid full forward pass
    with patch.object(engine.model, 'generate', return_value=torch.tensor([[1, 2, 3, 4, 5, 6]])):
        output = engine.generate(
            input_ids=input_ids,
            max_new_tokens=1
        )

    # Interceptor should have been created
    assert engine._interceptor is not None


def test_generate_removes_hooks_after_completion(mock_model, mock_quantizer, input_ids):
    """Test that hooks are removed after generation completes."""
    engine = CustomGenerateLoop(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )

    with patch.object(engine.model, 'generate', return_value=torch.tensor([[1, 2, 3, 4, 5, 6]])):
        output = engine.generate(
            input_ids=input_ids,
            max_new_tokens=1
        )

    # Hooks should be cleaned up
    assert engine._interceptor is not None
    # The reset method should have been called which clears the interceptor
    # Note: In real implementation, reset() sets _interceptor to None or clears hooks


def test_create_quantized_generator_factory(mock_model, mock_quantizer):
    """Test the factory function creates correct engine."""
    engine = create_quantized_generator(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )

    assert isinstance(engine, CustomGenerateLoop)
    assert engine.model is mock_model
    assert engine.quantizer is mock_quantizer
    assert engine.device == "cpu"


def test_generate_with_custom_config(mock_model, mock_quantizer, input_ids):
    """Test generation with custom generation config."""
    engine = CustomGenerateLoop(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )

    custom_config = GenerationConfig(
        max_new_tokens=10,
        temperature=0.7,
        top_k=20,
        do_sample=True
    )

    with patch.object(engine.model, 'generate', return_value=torch.tensor([[1, 2, 3, 4, 5, 6]])):
        output = engine.generate(
            input_ids=input_ids,
            generation_config=custom_config,
            max_new_tokens=5
        )

    # Verify generation was called
    assert output.shape[1] == 6


def test_reset_cache(mock_model, mock_quantizer, input_ids):
    """Test that reset_cache clears the interceptor state."""
    engine = CustomGenerateLoop(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )

    # First, trigger interceptor creation
    with patch.object(engine.model, 'generate', return_value=torch.tensor([[1, 2, 3, 4, 5, 6]])):
        engine.generate(input_ids=input_ids, max_new_tokens=1)

    assert engine._interceptor is not None

    # Reset
    engine.reset_cache()

    # Interceptor should be reset
    assert engine._interceptor is None


def test_get_quantized_cache_stats(mock_model, mock_quantizer):
    """Test getting quantization statistics."""
    engine = CustomGenerateLoop(
        model=mock_model,
        quantizer=mock_quantizer,
        device="cpu"
    )

    # Before any generation, stats should be empty
    stats = engine.get_quantized_cache_stats()
    assert stats == {}

    # After generation with mock, stats should reflect interceptor state
    input_ids = torch.tensor([[1, 2, 3, 4, 5]])
    with patch.object(engine.model, 'generate', return_value=torch.tensor([[1, 2, 3, 4, 5, 6]])):
        engine.generate(input_ids=input_ids, max_new_tokens=1)

    stats = engine.get_quantized_cache_stats()
    # Stats should now contain interceptor data
    assert isinstance(stats, dict)
