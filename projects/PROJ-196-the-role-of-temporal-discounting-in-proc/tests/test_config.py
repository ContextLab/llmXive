"""
Unit tests for the configuration module (code/config.py).

Verifies that project paths, environment variables, and random state
management work as expected.
"""
import os
import numpy as np
from config import get_project_root, get_config, get_random_state

def test_get_project_root_exists():
    """Test that the project root path is valid and exists."""
    root = get_project_root()
    assert root.exists(), f"Project root path does not exist: {root}"
    assert root.is_dir(), f"Project root is not a directory: {root}"

def test_get_config_returns_dict():
    """Test that get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict), "Config should be a dictionary"
    assert "project" in config, "Config should contain 'project' key"

def test_get_random_state_deterministic():
    """Test that get_random_state produces reproducible results."""
    rs1 = get_random_state()
    rs2 = get_random_state()
    
    # Generate numbers from both states
    val1 = rs1.random()
    val2 = rs2.random()
    
    # Should be identical if seeded identically
    assert val1 == val2, "Random states should produce identical sequences"

def test_random_state_type():
    """Test that get_random_state returns a valid numpy RandomState."""
    rs = get_random_state()
    assert isinstance(rs, np.random.RandomState), \
        "get_random_state should return np.random.RandomState instance"
