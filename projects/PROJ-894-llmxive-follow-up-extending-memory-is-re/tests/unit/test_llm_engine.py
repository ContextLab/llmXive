"""
Unit tests for the LLM Inference Engine.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from utils.llm_engine import LLMInferenceEngine, run_inference, DEFAULT_MODEL_PATH


class TestLLMInferenceEngine:
    """Tests for the LLMInferenceEngine class."""

    def test_init_model_not_found(self, tmp_path):
        """Test that initialization raises FileNotFoundError if model is missing."""
        fake_path = str(tmp_path / "nonexistent.gguf")
        with pytest.raises(FileNotFoundError):
            LLMInferenceEngine(model_path=fake_path)

    @patch('utils.llm_engine.Llama')
    def test_init_success(self, mock_llama_class, tmp_path):
        """Test successful model initialization."""
        # Mock the file existence check
        model_file = tmp_path / "model.gguf"
        model_file.touch()

        mock_instance = MagicMock()
        mock_llama_class.return_value = mock_instance

        engine = LLMInferenceEngine(model_path=str(model_file))

        assert engine.model_path == str(model_file)
        assert engine.model is mock_instance
        mock_llama_class.assert_called_once()

    @patch('utils.llm_engine.Llama')
    def test_run_inference(self, mock_llama_class, tmp_path):
        """Test that run_inference calls the model correctly."""
        model_file = tmp_path / "model.gguf"
        model_file.touch()

        mock_instance = MagicMock()
        mock_output = {
            'choices': [{'text': 'This is a generated response.'}]
        }
        mock_instance.return_value = mock_output
        mock_llama_class.return_value = mock_instance

        engine = LLMInferenceEngine(model_path=str(model_file))
        response = engine.run_inference("Test prompt")

        assert response == "This is a generated response."
        mock_instance.assert_called_once()

def test_run_inference_function():
    """Test the standalone run_inference function."""
    # This test verifies the function signature and basic flow
    # Actual execution requires a real model file which is not present in unit tests
    with patch('utils.llm_engine.LLMInferenceEngine') as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine.run_inference.return_value = "Mocked response"
        mock_engine_class.return_value = mock_engine

        result = run_inference("fake_path.gguf", "Test prompt")

        assert result == "Mocked response"
        mock_engine_class.assert_called_once_with(model_path="fake_path.gguf")
        mock_engine.run_inference.assert_called_once_with("Test prompt", 256, 0.7)