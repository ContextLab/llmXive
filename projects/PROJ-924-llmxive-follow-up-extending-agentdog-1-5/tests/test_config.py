"""
Unit tests for config.py constants and utilities.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import (
    RANDOM_SEED,
    MAX_RAM_GB,
    BATCH_SIZE,
    get_config,
    set_seed,
    get_path,
    ensure_directories
)

def test_config_constants():
    """Asserts the values in config.py match the task requirements."""
    assert RANDOM_SEED == 42, f"RANDOM_SEED must be 42, got {RANDOM_SEED}"
    assert MAX_RAM_GB == 7, f"MAX_RAM_GB must be 7, got {MAX_RAM_GB}"
    assert BATCH_SIZE == 64, f"BATCH_SIZE must be 64, got {BATCH_SIZE}"

def test_get_config():
    """Tests that get_config returns the expected dictionary."""
    config = get_config()
    assert isinstance(config, dict)
    assert config["RANDOM_SEED"] == 42
    assert config["MAX_RAM_GB"] == 7
    assert config["BATCH_SIZE"] == 64

def test_set_seed():
    """Tests that set_seed sets the random seeds correctly."""
    import random
    import numpy as np

    set_seed(123)
    val1 = random.random()
    arr1 = np.random.random()

    set_seed(123)
    val2 = random.random()
    arr2 = np.random.random()

    assert val1 == val2, "Random seed not set correctly for random module"
    np.testing.assert_array_equal(arr1, arr2, "Random seed not set correctly for numpy")

def test_get_path():
    """Tests that get_path returns a Path object."""
    # Test with a known key
    path = get_path("project_root")
    assert isinstance(path, Path)
    
    # Test that it resolves correctly (should be the project root or similar)
    # We just check it returns a valid Path object for now
    assert path.exists() or path.parent.exists(), f"Path {path} does not exist"

def test_ensure_directories():
    """Tests that ensure_directories creates directories."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_subdir"
        ensure_directories([str(test_dir)])
        assert test_dir.exists(), "ensure_directories failed to create directory"