"""
Unit tests for T004: Configuration Management verification logic.
"""
import pytest
import yaml
from pathlib import Path
import sys
import os

# Add the project code directory to the path to allow imports if needed,
# though we mostly test the logic inline or via the script execution.
CODE_DIR = Path(__file__).parent.parent.parent / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-" / "code"
sys.path.insert(0, str(CODE_DIR))

from verify_config import REQUIRED_SCHEMA, CONFIG_PATH

def test_schema_definition():
    """Verify that the schema dictionary is correctly defined."""
    assert "human_eval_url" in REQUIRED_SCHEMA
    assert REQUIRED_SCHEMA["human_eval_url"] == str
    assert REQUIRED_SCHEMA["max_cpu"] == int
    assert REQUIRED_SCHEMA["max_ram_gb"] == int

def test_config_file_exists():
    """Verify the config file exists at the expected path."""
    assert CONFIG_PATH.exists(), f"Config file missing at {CONFIG_PATH}"

def test_config_loads_valid_yaml():
    """Verify the config file contains valid YAML."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)

def test_config_types_match_schema():
    """Verify all keys in config match the expected types from schema."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for key, expected_type in REQUIRED_SCHEMA.items():
        assert key in data, f"Key {key} missing from config"
        value = data[key]
        # Handle yaml int/bool nuance if necessary, but strict type check first
        if expected_type == int:
            assert isinstance(value, int) and not isinstance(value, bool), \
                f"Key {key} must be int, got {type(value)}"
        else:
            assert isinstance(value, expected_type), \
                f"Key {key} must be {expected_type}, got {type(value)}"
