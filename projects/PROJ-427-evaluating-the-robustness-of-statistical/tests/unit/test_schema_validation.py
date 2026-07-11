"""
Unit tests for schema validation of error injection configuration.

This test verifies that:
1. The injection schema (contracts/injection.schema.yaml) is valid.
2. A sample config file (config/error_rates.yaml) conforms to the schema.
3. The 'error_rates' field is a non-empty list of floats.

This test is written BEFORE implementation tasks T020-T022 to ensure
schema consistency and validate the structure of deferred values.
"""
import os
import yaml
import pytest
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_PATH = BASE_DIR / "contracts" / "injection.schema.yaml"
CONFIG_PATH = BASE_DIR / "config" / "error_rates.yaml"

@pytest.fixture
def schema():
    """Load the injection schema."""
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def config():
    """Load the sample error rates config."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_schema_exists():
    """Ensure the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found: {SCHEMA_PATH}"

def test_config_exists():
    """Ensure the config file exists."""
    assert CONFIG_PATH.exists(), f"Config file not found: {CONFIG_PATH}"

def test_schema_valid_structure(schema):
    """Verify the schema defines the required properties."""
    assert "type" in schema, "Schema must define type"
    assert schema["type"] == "object", "Schema type must be object"
    assert "properties" in schema, "Schema must define properties"
    assert "error_rates" in schema["properties"], "Schema must define error_rates property"
    
    rates_prop = schema["properties"]["error_rates"]
    assert rates_prop["type"] == "array", "error_rates must be an array"
    assert "items" in rates_prop, "error_rates items must be defined"
    assert rates_prop["items"]["type"] == "number", "error_rates items must be numbers (floats)"
    assert rates_prop.get("minItems", 0) >= 1, "error_rates must be non-empty"

def test_config_error_rates_is_non_empty_list_of_floats(config):
    """
    Assert that error_rates is a non-empty list of floats.
    This validates the structure of the config without asserting specific rates.
    """
    assert "error_rates" in config, "Config must contain error_rates"
    
    rates = config["error_rates"]
    
    # Check it is a list
    assert isinstance(rates, list), "error_rates must be a list"
    
    # Check it is non-empty
    assert len(rates) > 0, "error_rates must be a non-empty list"
    
    # Check all items are floats (or numbers)
    for i, rate in enumerate(rates):
        assert isinstance(rate, (int, float)), f"Item {i} in error_rates must be a number, got {type(rate)}"
        # Ensure it's not a boolean (which is a subclass of int in Python)
        assert not isinstance(rate, bool), f"Item {i} in error_rates must be a number, not a boolean"

def test_config_conforms_to_schema(schema, config):
    """
    Basic structural conformance check.
    Note: A full JSON Schema validator could be used here, but for this task
    we verify the specific requirements mentioned in the task description.
    """
    # Verify top-level keys match schema properties
    for key in schema.get("properties", {}):
        assert key in config, f"Config missing required key: {key}"
    
    # Verify error_rates structure specifically
    rates = config.get("error_rates", [])
    schema_rates = schema.get("properties", {}).get("error_rates", {})
    
    assert isinstance(rates, list), "Config error_rates must be a list"
    assert len(rates) >= schema_rates.get("minItems", 1), "Config error_rates must be non-empty"
    
    for rate in rates:
        assert isinstance(rate, (int, float)) and not isinstance(rate, bool)
