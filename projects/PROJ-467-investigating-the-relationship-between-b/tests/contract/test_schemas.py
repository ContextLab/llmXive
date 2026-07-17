"""
Contract tests for JSON schemas defined in contracts/.
Validates that the schemas are syntactically correct and can be loaded.
"""
import json
import yaml
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def test_raw_dataset_schema_exists():
    """Verify raw_dataset.schema.yaml exists."""
    schema_path = CONTRACTS_DIR / "raw_dataset.schema.yaml"
    assert schema_path.exists(), f"Schema file not found: {schema_path}"

def test_raw_dataset_schema_valid_yaml():
    """Verify raw_dataset.schema.yaml is valid YAML."""
    schema_path = CONTRACTS_DIR / "raw_dataset.schema.yaml"
    try:
        with open(schema_path, "r") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "$schema" in schema, "Schema must define $schema version"
        assert "required" in schema, "Schema must define required fields"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in raw_dataset.schema.yaml: {e}")

def test_network_metric_schema_exists():
    """Verify network_metric.schema.yaml exists."""
    schema_path = CONTRACTS_DIR / "network_metric.schema.yaml"
    assert schema_path.exists(), f"Schema file not found: {schema_path}"

def test_network_metric_schema_valid_yaml():
    """Verify network_metric.schema.yaml is valid YAML."""
    schema_path = CONTRACTS_DIR / "network_metric.schema.yaml"
    try:
        with open(schema_path, "r") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "$schema" in schema, "Schema must define $schema version"
        assert "required" in schema, "Schema must define required fields"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in network_metric.schema.yaml: {e}")

def test_raw_dataset_schema_valid_json_schema():
    """Verify raw_dataset.schema.yaml conforms to JSON Schema draft-07."""
    schema_path = CONTRACTS_DIR / "raw_dataset.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # Basic structural checks for JSON Schema draft-07
    assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
    assert schema.get("type") == "object"
    assert "properties" in schema
    assert "subject_id" in schema["properties"]
    assert "tactile_score" in schema["properties"]

def test_network_metric_schema_valid_json_schema():
    """Verify network_metric.schema.yaml conforms to JSON Schema draft-07."""
    schema_path = CONTRACTS_DIR / "network_metric.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # Basic structural checks for JSON Schema draft-07
    assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
    assert schema.get("type") == "object"
    assert "properties" in schema
    assert "modularity_q" in schema["properties"]
    assert "flexibility" in schema["properties"]