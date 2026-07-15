"""
Unit tests for configuration loading.
"""
import pytest
from config import get_model_path, get_huggingface_cache_dir

def test_get_model_path_default():
    """Test getting the default model path."""
    path = get_model_path()
    assert path is not None
    assert isinstance(path, str)

def test_get_huggingface_cache_dir():
    """Test getting the cache directory."""
    cache_dir = get_huggingface_cache_dir()
    assert cache_dir is not None
    assert isinstance(cache_dir, str)
