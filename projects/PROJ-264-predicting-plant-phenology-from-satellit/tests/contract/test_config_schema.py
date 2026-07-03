"""
Contract tests for config.py against contracts/config_schema.json.

This module validates that the Config dataclass and its JSON serialization
strictly adhere to the schema defined in contracts/config_schema.json.
"""
import json
import os
import pytest
from pathlib import Path

# Import the real Config class from the existing API surface
from src.config import Config, get_config

# Path to the schema relative to project root
SCHEMA_PATH = Path("contracts/config_schema.json")


@pytest.fixture
def schema():
    """Load the JSON schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def config_instance():
    """Generate a valid Config instance using the real get_config logic."""
    # Ensure required env vars are set if the schema requires them, 
    # or use defaults if the schema allows. 
    # We rely on get_config() which handles defaults/overrides.
    try:
        cfg = get_config()
        return cfg
    except Exception as e:
        pytest.fail(f"Failed to instantiate Config: {e}")


def test_config_serializes_to_valid_json(config_instance):
    """Ensure the Config instance can be serialized to valid JSON."""
    try:
        json_str = config_instance.to_json()
        assert json_str is not None
        assert isinstance(json_str, str)
        # Verify it parses back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
    except AttributeError:
        # If to_json is not implemented, we check dict conversion if available
        # or fail if the contract requires JSON serialization.
        # Based on typical dataclass patterns, we assume to_json or asdict exists.
        if hasattr(config_instance, 'asdict'):
            json_str = json.dumps(config_instance.asdict())
            json.loads(json_str)
        else:
            pytest.fail("Config instance lacks JSON serialization method (to_json or asdict)")


def test_config_against_schema(schema, config_instance):
    """Validate the Config JSON output against the JSON Schema."""
    pytest.importorskip("jsonschema")
    from jsonschema import validate, ValidationError

    # Serialize the config to a dict for validation
    if hasattr(config_instance, 'to_json'):
        config_json = json.loads(config_instance.to_json())
    elif hasattr(config_instance, 'asdict'):
        config_json = config_instance.asdict()
    else:
        # Fallback: try to access public attributes if dataclass
        config_json = {
            k: v for k, v in vars(config_instance).items() 
            if not k.startswith('_')
        }

    try:
        validate(instance=config_json, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Config validation failed against schema: {e.message}")


def test_required_fields_exist(schema, config_instance):
    """Verify that all required fields in the schema are present in the Config."""
    required_fields = schema.get("required", [])
    
    # Get available keys from the config instance
    if hasattr(config_instance, 'to_json'):
        config_json = json.loads(config_instance.to_json())
    elif hasattr(config_instance, 'asdict'):
        config_json = config_instance.asdict()
    else:
        config_json = {k: v for k, v in vars(config_instance).items() if not k.startswith('_')}

    missing_fields = [f for f in required_fields if f not in config_json]
    
    if missing_fields:
        pytest.fail(f"Missing required fields in Config: {missing_fields}")
