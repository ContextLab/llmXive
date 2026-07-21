"""
Unit tests for VLM wrapper (T017).

Tests the VLMWrapper class for Phi-3-mini-4k-instruct-GGUF using llama-cpp-python.
"""
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.vlm import VLMWrapper, create_vlm_wrapper, DEFAULT_BATCH_SIZE


class MockLlama:
    """Mock class to simulate llama-cpp Llama model."""
    
    def __init__(self, *args, **kwargs):
        self.n_vocab_val = 32000
        self.n_ctx_train_val = 4096
    
    def n_vocab(self):
        return self.n_vocab_val
    
    def n_ctx_train(self):
        return self.n_ctx_train_val
    
    def __call__(self, prompt, max_tokens=512, temperature=0.7, stop=None, echo=False):
        return {
            'choices': [
                {
                    'text': f"Mock description for: {prompt[:50]}..."
                }
            ]
        }


@pytest.fixture
def mock_llama_cpp():
    """Mock the llama-cpp-python import."""
    with patch.dict('sys.modules', {'llama_cpp': MagicMock()}):
        from llama_cpp import Llama
        Llama = MockLlama
        yield


@pytest.fixture
def mock_hf_download():
    """Mock the HuggingFace download function."""
    with patch('src.models.vlm.hf_hub_download') as mock_download:
        mock_download.return_value = "/mock/path/Phi-3-mini-4k-instruct.Q4_K_M.gguf"
        yield mock_download


def test_vlm_wrapper_initialization(mock_hf_download):
    """Test that VLMWrapper initializes correctly with default parameters."""
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    
    assert wrapper.batch_size == DEFAULT_BATCH_SIZE
    assert wrapper.n_ctx == 4096
    assert wrapper.model_path == "/mock/path/Phi-3-mini-4k-instruct.Q4_K_M.gguf"
    assert wrapper.model is None  # Not loaded yet


def test_vlm_load_model(mock_llama_cpp, mock_hf_download):
    """Test that the model loads correctly."""
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    
    # Mock the Llama class import
    with patch('src.models.vlm.Llama', MockLlama):
        wrapper.load_model()
    
    assert wrapper.model is not None
    assert isinstance(wrapper.model, MockLlama)


def test_generate_description(mock_llama_cpp, mock_hf_download, tmp_path):
    """Test single image description generation."""
    # Create a dummy image file
    dummy_image = tmp_path / "test_image.png"
    dummy_image.write_bytes(b"dummy image content")
    
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    
    with patch('src.models.vlm.Llama', MockLlama):
        wrapper.load_model()
        description = wrapper.generate_description(str(dummy_image))
    
    assert isinstance(description, str)
    assert len(description) > 0
    assert "Mock description" in description


def test_generate_batch(mock_llama_cpp, mock_hf_download, tmp_path):
    """Test batch description generation."""
    # Create multiple dummy image files
    image_paths = []
    for i in range(3):
        dummy_image = tmp_path / f"test_image_{i}.png"
        dummy_image.write_bytes(b"dummy image content")
        image_paths.append(str(dummy_image))
    
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    
    with patch('src.models.vlm.Llama', MockLlama):
        wrapper.load_model()
        descriptions = wrapper.generate_batch(image_paths)
    
    assert isinstance(descriptions, list)
    assert len(descriptions) == 3
    for desc in descriptions:
        assert isinstance(desc, str)
        assert len(desc) > 0


def test_vlm_default_batch_size(mock_hf_download):
    """Test that the default batch size is 8."""
    wrapper = VLMWrapper()
    assert wrapper.batch_size == 8


def test_adjust_batch_size(mock_hf_download):
    """Test batch size adjustment."""
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    
    assert wrapper.batch_size == 8
    wrapper.adjust_batch_size(16)
    assert wrapper.batch_size == 16


def test_get_model_info_not_loaded(mock_hf_download):
    """Test model info when not loaded."""
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    info = wrapper.get_model_info()
    
    assert info["status"] == "not_loaded"
    assert "model_path" in info


def test_get_model_info_loaded(mock_llama_cpp, mock_hf_download):
    """Test model info when loaded."""
    wrapper = VLMWrapper(batch_size=DEFAULT_BATCH_SIZE)
    
    with patch('src.models.vlm.Llama', MockLlama):
        wrapper.load_model()
    
    info = wrapper.get_model_info()
    
    assert info["status"] == "loaded"
    assert info["n_vocab"] == 32000
    assert info["n_ctx_train"] == 4096