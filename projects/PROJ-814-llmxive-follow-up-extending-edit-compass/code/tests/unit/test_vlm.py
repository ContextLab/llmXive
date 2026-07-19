"""
Unit tests for VLM wrapper (T017).
Tests the initialization and prompt construction logic without heavy inference.
"""
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Mock the llama_cpp import to avoid heavy dependencies in unit tests
@pytest.fixture(autouse=True)
def mock_llama_cpp(monkeypatch):
    mock_llama = MagicMock()
    mock_llama.return_value.__getitem__ = MagicMock(return_value={"choices": [{"text": "mocked description"}]})
    monkeypatch.setattr("llama_cpp.Llama", mock_llama)
    return mock_llama

@pytest.fixture(autouse=True)
def mock_hf_download(monkeypatch):
    # Mock the download to return a fake path
    monkeypatch.setattr("src.models.vlm.hf_hub_download", lambda **kwargs: "/fake/path/model.gguf")
    return None

def test_vlm_wrapper_initialization():
    """Test that VLMWrapper initializes with correct parameters."""
    from src.models.vlm import VLMWrapper, DEFAULT_BATCH_SIZE
    
    # Should not raise
    wrapper = VLMWrapper(n_batch=4, n_threads=2)
    
    assert wrapper.n_batch == 4
    assert wrapper.n_threads == 2
    assert wrapper.model_path == "/fake/path/model.gguf"
    assert wrapper.model is None  # Lazy load

def test_vlm_load_model(mock_llama_cpp):
    """Test that load_model instantiates the Llama class."""
    from src.models.vlm import VLMWrapper
    
    wrapper = VLMWrapper(n_batch=2)
    wrapper.load_model()
    
    assert wrapper.model is not None
    mock_llama_cpp.assert_called_once()

def test_generate_description(mock_llama_cpp):
    """Test single description generation."""
    from src.models.vlm import VLMWrapper
    
    wrapper = VLMWrapper(n_batch=2)
    wrapper.load_model()
    
    result = wrapper.generate_description(instruction="Change the color to red")
    
    assert isinstance(result, str)
    assert result == "mocked description"

def test_generate_batch(mock_llama_cpp):
    """Test batch generation."""
    from src.models.vlm import VLMWrapper
    
    wrapper = VLMWrapper(n_batch=2)
    wrapper.load_model()
    
    items = [
        {"instruction": "Make it blue"},
        {"instruction": "Make it green"},
        {"instruction": "Make it red"}
    ]
    
    results = wrapper.generate_batch(items)
    
    assert len(results) == 3
    assert all(isinstance(r, str) for r in results)

def test_vlm_default_batch_size():
    """Test that default batch size is 8 as per requirement."""
    from src.models.vlm import DEFAULT_BATCH_SIZE
    assert DEFAULT_BATCH_SIZE == 8