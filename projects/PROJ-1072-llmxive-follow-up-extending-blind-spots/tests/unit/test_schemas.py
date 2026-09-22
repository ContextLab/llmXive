"""
Unit tests for YAML schema definitions.
Validates that the schema files are syntactically correct YAML
and contain the required top-level keys.
"""
import json
import yaml
import pytest
from pathlib import Path

# Paths relative to project root
CONTRACTS_DIR = Path("specs/001-blind-spots-order-analysis/contracts")

SCHEMAS = {
    "task-record": CONTRACTS_DIR / "task-record.schema.yaml",
    "cot-trace": CONTRACTS_DIR / "cot-trace.schema.yaml",
    "analysis-result": CONTRACTS_DIR / "analysis-result.schema.yaml",
}

REQUIRED_KEYS = {
    "task-record": ["title", "type", "properties", "required"],
    "cot-trace": ["title", "type", "properties", "required"],
    "analysis-result": ["title", "type", "properties", "required"],
}


@pytest.mark.parametrize("schema_name, path", SCHEMAS.items())
def test_schema_file_exists(schema_name, path):
    """Verify that the schema file exists on disk."""
    assert path.exists(), f"Schema file {path} does not exist."


@pytest.mark.parametrize("schema_name, path", SCHEMAS.items())
def test_schema_is_valid_yaml(schema_name, path):
    """Verify that the schema file is valid YAML."""
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            assert isinstance(data, dict), f"Schema {schema_name} is not a dictionary."
        except yaml.YAMLError as e:
            pytest.fail(f"Schema {schema_name} is not valid YAML: {e}")


@pytest.mark.parametrize("schema_name, path", SCHEMAS.items())
def test_schema_has_required_keys(schema_name, path):
    """Verify that the schema contains required top-level keys."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    required = REQUIRED_KEYS[schema_name]
    missing = [key for key in required if key not in data]
    
    assert not missing, f"Schema {schema_name} is missing required keys: {missing}"


def test_task_record_schema_properties():
    """Verify specific properties in task-record schema."""
    path = SCHEMAS["task-record"]
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    props = data.get("properties", {})
    assert "task_id" in props
    assert "constraint" in props
    assert "category" in props
    
    # Check that 'constraint' is required
    assert "constraint" in data.get("required", [])


def test_cot_trace_schema_properties():
    """Verify specific properties in cot-trace schema."""
    path = SCHEMAS["cot-trace"]
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    props = data.get("properties", {})
    assert "trace_id" in props
    assert "parse_result" in props
    assert "classification" in props
    
    # Check nested structure
    parse_result = props.get("parse_result", {}).get("properties", {})
    assert "first_mention" in parse_result
    assert "last_mention" in parse_result


def test_analysis_result_schema_properties():
    """Verify specific properties in analysis-result schema."""
    path = SCHEMAS["analysis-result"]
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    props = data.get("properties", {})
    assert "analysis_id" in props
    assert "category_stats" in props
    assert "hypothesis_tests" in props
    assert "framing" in props
    
    # Check framing enum
    framing_prop = props.get("framing", {})
    assert framing_prop.get("enum") == ["Associational"]