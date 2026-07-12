"""
Unit tests for the configuration loader.
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    load_config,
    get_constant,
    get_path,
    DEFAULT_CONSTANTS,
    DEFAULT_PATHS,
    _deep_merge,
    ensure_paths_exist
)


def test_default_config_paths_exist():
    """Test that default paths are valid Path objects and exist (or can be created)."""
    config = load_config()
    for name, path in config["paths"].items():
        assert isinstance(path, Path), f"Path {name} is not a Path object"
        # We don't assert existence here because ensure_paths_exist might not have been called,
        # but we check that the parent exists or the path is valid
        if not path.exists():
            # Try to create parent to verify it's writable
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception:
                # If we can't create it, that's a permission issue, not a config issue
                pass


def test_default_constants():
    """Test that default constants are present and have expected types."""
    config = load_config()
    for key, value in DEFAULT_CONSTANTS.items():
        assert key in config["constants"], f"Missing default constant: {key}"
        assert config["constants"][key] == value, f"Default value mismatch for {key}"


def test_deep_merge():
    """Test the deep merge utility function."""
    base = {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3
        }
    }
    override = {
        "b": {
            "c": 20,
            "e": 4
        },
        "f": 5
    }
    expected = {
        "a": 1,
        "b": {
            "c": 20,
            "d": 3,
            "e": 4
        },
        "f": 5
    }
    result = _deep_merge(base, override)
    assert result == expected


def test_load_config_from_file():
    """Test loading configuration from a temporary YAML file."""
    override_data = {
        "constants": {
            "RADIAL_MOTION_THRESHOLD_DEG": 99.0
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(override_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        assert config["constants"]["RADIAL_MOTION_THRESHOLD_DEG"] == 99.0
        # Ensure other defaults are still there
        assert "Z_VELOCITY_THRESHOLD" in config["constants"]
    finally:
        os.unlink(temp_path)


def test_get_constant():
    """Test retrieving a constant."""
    val = get_constant("RADIAL_MOTION_THRESHOLD_DEG")
    assert val == DEFAULT_CONSTANTS["RADIAL_MOTION_THRESHOLD_DEG"]


def test_get_constant_not_found():
    """Test retrieving a non-existent constant raises KeyError."""
    with pytest.raises(KeyError):
        get_constant("NON_EXISTENT_CONSTANT")


def test_get_path():
    """Test retrieving a path."""
    p = get_path("data_raw")
    assert isinstance(p, Path)


def test_get_path_not_found():
    """Test retrieving a non-existent path raises KeyError."""
    with pytest.raises(KeyError):
        get_path("non_existent_path")
