"""
Unit tests for data model contracts (T007).
Validates that schema definitions are syntactically correct and loadable.
"""
import os
import yaml
import pytest
import jsonschema

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "specs", "contracts")

@pytest.fixture
def state_schema_path():
    return os.path.join(CONTRACTS_DIR, "state_snapshot.schema.yaml")

@pytest.fixture
def metric_schema_path():
    return os.path.join(CONTRACTS_DIR, "metric_result.schema.yaml")

def test_state_snapshot_schema_exists(state_schema_path):
    """Verify state_snapshot.schema.yaml exists."""
    assert os.path.exists(state_schema_path), f"Schema file not found: {state_schema_path}"

def test_metric_result_schema_exists(metric_schema_path):
    """Verify metric_result.schema.yaml exists."""
    assert os.path.exists(metric_schema_path), f"Schema file not found: {metric_schema_path}"

def test_state_snapshot_schema_valid_yaml(state_schema_path):
    """Verify state_snapshot.schema.yaml is valid YAML."""
    try:
        with open(state_schema_path, "r") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict)
        assert "properties" in schema
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in state_snapshot.schema.yaml: {e}")

def test_metric_result_schema_valid_yaml(metric_schema_path):
    """Verify metric_result.schema.yaml is valid YAML."""
    try:
        with open(metric_schema_path, "r") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict)
        assert "properties" in schema
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in metric_result.schema.yaml: {e}")

def test_state_snapshot_schema_valid_json_schema(state_schema_path):
    """Verify state_snapshot.schema.yaml is valid JSON Schema draft-07."""
    with open(state_schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # Basic structural checks for JSON Schema draft-07
    assert "$schema" in schema
    assert "http://json-schema.org/draft-07/schema#" in schema["$schema"]
    assert "type" in schema
    assert schema["type"] == "object"
    assert "required" in schema
    assert isinstance(schema["required"], list)

def test_metric_result_schema_valid_json_schema(metric_schema_path):
    """Verify metric_result.schema.yaml is valid JSON Schema draft-07."""
    with open(metric_schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # Basic structural checks for JSON Schema draft-07
    assert "$schema" in schema
    assert "http://json-schema.org/draft-07/schema#" in schema["$schema"]
    assert "type" in schema
    assert schema["type"] == "object"
    assert "required" in schema
    assert isinstance(schema["required"], list)

def test_state_snapshot_sample_data_validates(state_schema_path):
    """Test a sample state snapshot against the schema."""
    with open(state_schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    sample_data = {
        "timestamp": 10,
        "grid_dimensions": {"width": 10, "height": 10},
        "agent_position": {"x": 5, "y": 5},
        "visible_items": [
            {"type": "key", "position": {"x": 5, "y": 6}, "state": "unlocked"}
        ],
        "hidden_items": [
            {"type": "door", "position": {"x": 8, "y": 8}, "state": "locked"}
        ],
        "game_status": "active"
    }
    
    try:
        jsonschema.validate(instance=sample_data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Sample data failed validation: {e.message}")

def test_metric_result_sample_data_validates(metric_schema_path):
    """Test a sample metric result against the schema."""
    with open(metric_schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    sample_data = {
        "run_id": "run-001",
        "seed": 42,
        "metric_name": "memory_gap",
        "value": 0.15,
        "timestamp": "2023-10-27T10:00:00Z",
        "agent_type": "text_agent",
        "details": {
            "missing_items_count": 1
        }
    }
    
    try:
        jsonschema.validate(instance=sample_data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Sample data failed validation: {e.message}")

def test_state_snapshot_required_fields(state_schema_path):
    """Verify required fields are defined in state snapshot schema."""
    with open(state_schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    required_fields = ["timestamp", "grid_dimensions", "agent_position", "visible_items", "hidden_items", "game_status"]
    for field in required_fields:
        assert field in schema["required"], f"Missing required field: {field}"

def test_metric_result_required_fields(metric_schema_path):
    """Verify required fields are defined in metric result schema."""
    with open(metric_schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    required_fields = ["run_id", "seed", "metric_name", "value", "timestamp"]
    for field in required_fields:
        assert field in schema["required"], f"Missing required field: {field}"
