"""
Unit tests for lint configuration validation.

This module verifies that the .ruff.toml file exists at the project root
and is syntactically valid according to the project's linting requirements.
"""
import os
import pytest
from pathlib import Path
import tomli  # Using tomli for TOML parsing as it's the standard for Python 3.11+ compatible reading

# Fallback for older Python versions if tomli is not available
try:
    import tomllib
except ImportError:
    tomllib = tomli  # type: ignore
    
# Standard library fallback for TOML if no external lib is present (Python < 3.11)
# However, requirements.txt usually includes tomli for consistency.
# We will attempt to use tomli/tomllib, and if that fails, we'll use a basic existence check.

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume tests/unit is two levels deep from root
    return Path(__file__).resolve().parent.parent.parent

def test_ruff_config_exists():
    """Verify that .ruff.toml exists at the project root."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    
    assert config_path.exists(), f"File .ruff.toml not found at {config_path}"
    assert config_path.is_file(), f"{config_path} is not a file"

def test_ruff_config_valid_syntax():
    """Verify that .ruff.toml contains valid TOML syntax."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    
    try:
        with open(config_path, "rb") as f:
            # Parse TOML to ensure it's valid
            tomllib.load(f)
    except Exception as e:
        pytest.fail(f".ruff.toml contains invalid TOML syntax: {e}")

def test_ruff_config_required_keys():
    """Verify that .ruff.toml contains the required configuration keys."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    # Check for max-line-length
    assert "max-line-length" in config, "Missing required key: max-line-length"
    assert config["max-line-length"] == 88, f"max-line-length should be 88, got {config['max-line-length']}"
    
    # Check for select rules
    assert "select" in config, "Missing required key: select"
    required_select = ["E", "F", "I"]
    for rule in required_select:
        assert rule in config["select"], f"Missing required rule in select: {rule}"