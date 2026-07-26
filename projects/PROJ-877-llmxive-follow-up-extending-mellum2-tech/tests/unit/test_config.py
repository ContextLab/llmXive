"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
import random

# Import the module directly since conftest adds it to path
from config import set_seed, ensure_dirs, get_config

def test_set_seed_determinism():
    """Verify that set_seed produces deterministic random states."""
    set_seed(42)
    val1 = random.random()
    
    set_seed(42)
    val2 = random.random()
    
    assert val1 == val2, "Random seed did not produce deterministic results"

def test_ensure_dirs_creates_structure(tmp_path):
    """Verify that ensure_dirs creates the required directory structure."""
    # Override base path for testing
    test_base = tmp_path / "test_project"
    ensure_dirs(test_base)
    
    # Check expected directories exist
    assert (test_base / "code").exists()
    assert (test_base / "data").exists()
    assert (test_base / "tests").exists()
    assert (test_base / "data" / "raw").exists()
    assert (test_base / "data" / "processed").exists()
    assert (test_base / "data" / "results").exists()
    assert (test_base / "figures").exists()

def test_get_config_returns_dict():
    """Verify get_config returns a dictionary with expected keys."""
    config = get_config()
    assert isinstance(config, dict)
    assert "seed" in config
    assert "data_dir" in config
    assert "code_dir" in config
