"""
Unit tests for config module.
"""
import pytest
from config import get_model_path, get_huggingface_cache_dir

def test_get_model_path_default():
    """Test that default model path is returned when no env var is set."""
    # Ensure env var is not set
    import os
    os.environ.pop("LLMXIVE_MODEL_PATH", None)
    
    path = get_model_path()
    # Should return the default Llama-2-7B path
    assert "Llama-2-7B" in path or "Llama-2-13B" in path

def test_get_model_path_env():
    """Test that env var overrides default model path."""
    import os
    test_path = "/custom/path/to/model.gguf"
    os.environ["LLMXIVE_MODEL_PATH"] = test_path
    
    try:
        path = get_model_path()
        assert path == test_path
    finally:
        os.environ.pop("LLMXIVE_MODEL_PATH", None)

def test_get_huggingface_cache_dir():
    """Test that cache directory is returned correctly."""
    cache_dir = get_huggingface_cache_dir()
    assert cache_dir is not None
    assert isinstance(cache_dir, str)
