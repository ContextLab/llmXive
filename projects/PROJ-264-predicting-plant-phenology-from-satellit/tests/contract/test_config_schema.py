"""
Contract tests for config.py against contracts/config_schema.json.

Uses pytest-jsonschema to validate the generated configuration dictionary
against the JSON Schema definition.
"""
import json
import os
import pytest
import jsonschema
from pathlib import Path
from src.config import get_config

# Determine paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "config_schema.json"

@pytest.fixture
def config_schema():
    """Load the JSON Schema for configuration."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def config_dict():
    """Generate the configuration dictionary from the singleton."""
    # Force a fresh load if needed, or just get the current config
    # get_config() returns the Config dataclass, we need to serialize it
    cfg = get_config()
    # Convert dataclass to dict recursively
    def to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, (list, tuple)):
            return [to_dict(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        else:
            return obj
    
    return to_dict(cfg)

def test_config_validates_against_schema(config_dict, config_schema):
    """
    Verify that the runtime configuration dictionary conforms to the 
    JSON Schema defined in contracts/config_schema.json.
    """
    try:
        jsonschema.validate(instance=config_dict, schema=config_schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Config validation failed: {e.message} at {list(e.absolute_path)}")
    except jsonschema.SchemaError as e:
        pytest.fail(f"Schema itself is invalid: {e.message}")

def test_required_fields_present(config_dict, config_schema):
    """
    Explicitly check that all required fields from the schema are present
    in the generated config dictionary.
    """
    required_fields = config_schema.get("required", [])
    missing = []
    for field in required_fields:
        if field not in config_dict:
            missing.append(field)
    
    if missing:
        pytest.fail(f"Missing required config fields: {missing}")

def test_schema_file_is_valid_json():
    """Ensure the schema file itself is valid JSON."""
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file is not valid JSON: {e}")
