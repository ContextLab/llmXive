"""
Unit tests for configuration management (src/utils/config.py).
"""
import pytest
from pathlib import Path
import sys
import os

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_config, set_seed

def test_get_config_returns_dict():
    """Test that get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict)
    assert "random_seed" in config
    assert "project_root" in config

def test_set_seed_deterministic():
    """Test that setting a seed produces deterministic results."""
    import random
    
    set_seed(42)
    val1 = random.random()
    
    set_seed(42)
    val2 = random.random()
    
    assert val1 == val2
