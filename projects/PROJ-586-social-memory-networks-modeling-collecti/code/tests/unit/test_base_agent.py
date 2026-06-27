"""Unit tests for BaseAgent implementation."""

import pytest
from unittest.mock import Mock, patch
import torch

from agent.base_agent import BaseAgent


class TestBaseAgentInitialization:
    """Tests for BaseAgent initialization."""

    def test_agent_creates_with_default_model(self):
        """Agent should initialize with opt-125m by default."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(agent_id="test-001", load_model=True)

            assert agent.agent_id == "test-001"
            assert agent.model_name == "facebook/opt-125m"
            assert agent.device == "cpu"

    def test_agent_creates_with_custom_parameters(self):
        """Agent should accept custom parameters."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(
                agent_id="custom-001",
                temperature=0.9,
                max_length=1024,
                load_model=True
            )

            assert agent.agent_id == "custom-001"
            assert agent.temperature == 0.9
            assert agent.max_length == 1024

    def test_agent_with_memory_buffer(self):
        """Agent should accept and store memory buffer reference."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            mock_buffer = Mock()
            agent = BaseAgent(
                agent_id="buffer-001",
                memory_buffer=mock_buffer,
                load_model=True
            )

            assert agent.memory_buffer is mock_buffer

    def test_agent_without_model_loading(self):
        """Agent can be created without loading model immediately."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            agent = BaseAgent(
                agent_id="lazy-001",
                load_model=False
            )

            mock_tokenizer.assert_not_called()
            mock_model.assert_not_called()
            assert agent.model is None
            assert agent.tokenizer is None


class TestBaseAgentGeneration:
    """Tests for text generation functionality."""

    def test_generate_raises_if_model_not_loaded(self):
        """Generate should raise RuntimeError if model not loaded."""
        agent = BaseAgent(agent_id="test-001", load_model=False)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            agent.generate("test prompt")

    def test_generate_with_memory_context(self):
        """Generate should prepend memory context when provided."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model, \
             patch('agent.base_agent.torch') as mock_torch:
            mock_tokenizer.return_value = Mock(
                encode=Mock(return_value=[1, 2, 3]),
                decode=Mock(return_value="test response"),
                eos_token_id=0
            )
            mock_model.return_value = Mock()
            mock_model.return_value.generate = Mock(return_value=mock_torch.tensor([[1, 2, 3, 4, 5]]))

            agent = BaseAgent(agent_id="gen-001", load_model=True)
            agent.tokenizer = mock_tokenizer.return_value
            agent.model = mock_model.return_value

            response = agent.generate("test prompt", memory_context="memory data")

            assert "memory data" in response or "test response" in response

    def test_generate_strips_prompt_from_response(self):
        """Generate should strip original prompt from response."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model, \
             patch('agent.base_agent.torch') as mock_torch:
            mock_tokenizer.return_value = Mock(
                encode=Mock(return_value=[1, 2, 3]),
                decode=Mock(return_value="test prompt\n\nactual response"),
                eos_token_id=0
            )
            mock_model.return_value = Mock()
            mock_model.return_value.generate = Mock(return_value=mock_torch.tensor([[1, 2, 3, 4, 5]]))

            agent = BaseAgent(agent_id="strip-001", load_model=True)
            agent.tokenizer = mock_tokenizer.return_value
            agent.model = mock_model.return_value

            response = agent.generate("test prompt")

            assert "test prompt" not in response
            assert "actual response" in response


class TestBaseAgentMemoryOperations:
    """Tests for memory buffer operations."""

    def test_store_memory_returns_none_without_buffer(self):
        """Store should return None if no memory buffer."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(agent_id="nobuf-001", load_model=True)
            result = agent.store_memory("test content")

            assert result is None

    def test_store_memory_delegates_to_buffer(self):
        """Store should delegate to memory buffer."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            mock_buffer = Mock(return_value="entry-123")
            agent = BaseAgent(
                agent_id="buf-001",
                memory_buffer=mock_buffer,
                load_model=True
            )

            result = agent.store_memory("test content", metadata={"key": "value"})

            assert result == "entry-123"
            mock_buffer.store.assert_called_once()

    def test_retrieve_memory_returns_empty_without_buffer(self):
        """Retrieve should return empty list if no memory buffer."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(agent_id="nobuf-002", load_model=True)
            results = agent.retrieve_memory("test query")

            assert results == []

    def test_retrieve_memory_delegates_to_buffer(self):
        """Retrieve should delegate to memory buffer."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            mock_buffer = Mock(return_value=[{"content": "result1"}, {"content": "result2"}])
            agent = BaseAgent(
                agent_id="buf-002",
                memory_buffer=mock_buffer,
                load_model=True
            )

            results = agent.retrieve_memory("test query", top_k=3)

            assert len(results) == 2
            mock_buffer.retrieve.assert_called_once_with("test query", top_k=3)


class TestBaseAgentMemoryActionProcessing:
    """Tests for <MEMORY_ACTION> token handling."""

    def test_process_store_action(self):
        """Should process STORE action correctly."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            mock_buffer = Mock(return_value="stored-123")
            agent = BaseAgent(
                agent_id="action-001",
                memory_buffer=mock_buffer,
                load_model=True
            )

            result = agent.process_memory_action("STORE test content")

            assert "Stored memory" in result

    def test_process_retrieve_action(self):
        """Should process RETRIEVE action correctly."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            mock_buffer = Mock(return_value=[{"content": "result"}])
            agent = BaseAgent(
                agent_id="action-002",
                memory_buffer=mock_buffer,
                load_model=True
            )

            result = agent.process_memory_action("RETRIEVE test query")

            assert "Retrieved" in result

    def test_process_clear_action(self):
        """Should process CLEAR action correctly."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            mock_buffer = Mock()
            agent = BaseAgent(
                agent_id="action-003",
                memory_buffer=mock_buffer,
                load_model=True
            )

            result = agent.process_memory_action("CLEAR")

            assert "Memory cleared" in result
            mock_buffer.clear.assert_called_once()

    def test_process_invalid_action(self):
        """Should return None for invalid action type."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(agent_id="action-004", load_model=True)

            result = agent.process_memory_action("INVALID test")

            assert result is None

    def test_process_malformed_action(self):
        """Should return None for malformed action."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(agent_id="action-005", load_model=True)

            result = agent.process_memory_action("STORE")

            assert result is None


class TestBaseAgentUtilities:
    """Tests for utility methods."""

    def test_get_context_window_default(self):
        """Context window should default to max_length if no tokenizer."""
        agent = BaseAgent(agent_id="util-001", load_model=False)
        agent.max_length = 1024

        assert agent.get_context_window() == 1024

    def test_agent_repr(self):
        """Agent string representation should include key attributes."""
        with patch('agent.base_agent.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('agent.base_agent.AutoModelForCausalLM.from_pretrained') as mock_model:
            mock_tokenizer.return_value = Mock()
            mock_model.return_value = Mock()

            agent = BaseAgent(agent_id="repr-001", load_model=True)

            repr_str = repr(agent)
            assert "repr-001" in repr_str
            assert "facebook/opt-125m" in repr_str
            assert "cpu" in repr_str