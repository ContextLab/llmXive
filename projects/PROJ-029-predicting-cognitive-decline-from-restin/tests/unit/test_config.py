"""
Unit tests for configuration management.
"""
import pytest
from config import get_config

def test_get_config():
    """Test config retrieval."""
    cfg = get_config()
    assert cfg is not None
    assert 'random_seed' in cfg
