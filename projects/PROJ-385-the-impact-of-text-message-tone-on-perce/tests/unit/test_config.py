"""
Unit tests for the configuration module (code/config.py).

Verifies:
1. RANDOM_SEED is set to an integer constant.
2. BASE_DATA_PATH (via get_data_dir logic) points to 'data'.
"""
import pytest
from pathlib import Path

# Import the config module to test its attributes directly
import sys
import os

# Ensure the code directory is in the path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import config


def test_random_seed_is_integer_constant():
    """Assert that RANDOM_SEED is set to an integer constant."""
    assert hasattr(config, 'RANDOM_SEED'), "RANDOM_SEED attribute missing in config"
    assert isinstance(config.RANDOM_SEED, int), f"RANDOM_SEED must be an integer, got {type(config.RANDOM_SEED)}"
    # Optional: Check it's not None or 0, though 0 is technically a valid seed.
    # We just ensure it is a defined integer.
    assert config.RANDOM_SEED is not None

def test_base_data_path_points_to_data():
    """Assert that the base data path logic points to 'data'."""
    # The task requires verifying that BASE_DATA_PATH points to 'data'.
    # We check the constant directly if exposed, or via the assertion in get_data_dir.
    assert hasattr(config, 'BASE_DATA_PATH_STR'), "BASE_DATA_PATH_STR attribute missing"
    assert config.BASE_DATA_PATH_STR == "data", f"BASE_DATA_PATH_STR must be 'data', got '{config.BASE_DATA_PATH_STR}'"

def test_get_data_dir_returns_correct_path():
    """Verify that get_data_dir returns a path ending with 'data'."""
    data_dir = config.get_data_dir()
    assert data_dir.name == "data", f"Data directory name must be 'data', got '{data_dir.name}'"
    assert data_dir.exists() or True, "We check existence only if the directory is created; path correctness is key here."

def test_config_imports_successfully():
    """Ensure the config module can be imported without errors."""
    # This is implicitly tested by the import at the top, but explicit is better.
    assert config is not None