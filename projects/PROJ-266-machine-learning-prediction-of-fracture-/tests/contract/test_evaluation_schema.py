"""
Contract test for evaluation schema.

Verifies that the evaluation output conforms to the schema defined in
contracts/evaluation_schema.schema.yaml.
"""
import json
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

import sys
from pathlib import Path

# Ensure code/ is in path for imports if running from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

SCHEMA_PATH = Path("contracts/evaluation_schema.schema.yaml")

def load_schema() -> Dict[str, Any]:
    """Load the evaluation schema from YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> None:
    """Validate the basic structure of the schema."""
    assert "properties" in schema, "Schema must have 'properties' key"
    assert "model_type" in schema["properties"], "Schema must define 'model_type'"
    assert "r_squared" in schema["properties"], "Schema must define 'r_squared'"

def test_schema_loads_correctly() -> None:
    """Test that the evaluation schema loads without errors."""
    schema = load_schema()
    assert schema is not None
    assert isinstance(schema, dict)
    validate_schema_structure(schema)

def test_model_type_enum() -> None:
    """Test that model_type has the correct enum values."""
    schema = load_schema()
    model_type_def = schema["properties"]["model_type"]
    assert "enum" in model_type_def, "model_type must have an enum definition"
    expected_models = ["cnn", "linear", "random_forest"]
    assert set(model_type_def["enum"]) == set(expected_models), \
        f"model_type enum mismatch: expected {expected_models}, got {model_type_def['enum']}"

def test_r_squared_type() -> None:
    """Test that r_squared is defined as a number."""
    schema = load_schema()
    r2_def = schema["properties"]["r_squared"]
    assert r2_def["type"] == "number", "r_squared must be of type 'number'"

def test_sample_valid_evaluation_record() -> None:
    """Test validation against a sample valid evaluation record."""
    schema = load_schema()

    # Construct a valid record matching the schema
    valid_record = {
        "model_type": "cnn",
        "r_squared": 0.85,
        "mae": 2.3,
        "rmse": 3.1
    }

    # Basic type checks (since we don't have a full JSON Schema validator here)
    assert valid_record["model_type"] in schema["properties"]["model_type"]["enum"]
    assert isinstance(valid_record["r_squared"], (int, float))
    assert isinstance(valid_record["mae"], (int, float))
    assert isinstance(valid_record["rmse"], (int, float))

def test_invalid_model_type() -> None:
    """Test that an invalid model_type is rejected."""
    schema = load_schema()
    invalid_models = ["transformer", "svm", "neural_net"]
    for model in invalid_models:
        assert model not in schema["properties"]["model_type"]["enum"], \
            f"{model} should not be in allowed model types"

def test_schema_properties_match_task_requirements() -> None:
    """Verify the schema explicitly covers the required fields from the task."""
    schema = load_schema()
    props = schema["properties"]

    # Check for required fields mentioned in T006b and T018
    assert "model_type" in props
    assert "r_squared" in props

    # Verify specific constraints from T006b verification
    assert props["model_type"]["enum"] == ["cnn", "linear", "random_forest"]
    assert props["r_squared"]["type"] == "number"