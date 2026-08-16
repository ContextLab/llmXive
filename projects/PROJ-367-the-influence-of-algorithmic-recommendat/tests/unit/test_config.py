"""
Unit tests for code/config.py.

Verifies that configuration loading and path resolution work correctly.
"""
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from config import get_config, PROJECT_ROOT as CONFIG_PROJECT_ROOT


def test_get_config_returns_dict():
    """Test that get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict)


def test_config_contains_required_keys():
    """Test that the config contains essential keys."""
    config = get_config()
    required_keys = ["seed", "similarity_threshold", "data_path"]
    for key in required_keys:
        assert key in config, f"Missing required key: {key}"


def test_config_seed_is_integer():
    """Test that the seed is an integer."""
    config = get_config()
    assert isinstance(config["seed"], int)


def test_config_similarity_threshold_is_float():
    """Test that the similarity threshold is a float."""
    config = get_config()
    assert isinstance(config["similarity_threshold"], float)
    assert 0.0 <= config["similarity_threshold"] <= 1.0


def test_config_data_path_exists():
    """Test that the data path resolves to a valid Path object."""
    config = get_config()
    data_path = config["data_path"]
    assert isinstance(data_path, Path)
    # Note: The actual directory might not exist yet in a fresh environment,
    # but the path object should be valid.
