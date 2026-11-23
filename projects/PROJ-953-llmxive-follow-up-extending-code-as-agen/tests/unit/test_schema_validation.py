import json
import yaml
import pytest
from pathlib import Path
import jsonschema

# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "structural_metric.schema.yaml"

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T005 is completed.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def test_structural_metric_fallback_logic(schema):
    """
    Verify that the structural_metric.schema.yaml correctly enforces the conditional logic:
    - If 'semantic_complexity_score' is missing, 'lines_of_code' is REQUIRED.
    - If 'semantic_complexity_score' is present, 'lines_of_code' is optional.
    """
    
    # Case 1: Valid record with semantic_complexity_score (lines_of_code optional)
    valid_with_semantic = {
        "task_id": "test-1",
        "dependency_depth": 5,
        "cyclomatic_complexity": 10,
        "semantic_complexity_score": 0.85
    }
    try:
        jsonschema.validate(instance=valid_with_semantic, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Schema should accept record with semantic_complexity_score. Error: {e.message}")

    # Case 2: Valid record with lines_of_code fallback (semantic_complexity_score missing)
    valid_with_fallback = {
        "task_id": "test-2",
        "dependency_depth": 5,
        "cyclomatic_complexity": 10,
        "lines_of_code": 150
    }
    try:
        jsonschema.validate(instance=valid_with_fallback, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Schema should accept record with lines_of_code fallback. Error: {e.message}")

    # Case 3: Invalid record - missing BOTH semantic_complexity_score and lines_of_code
    invalid_missing_both = {
        "task_id": "test-3",
        "dependency_depth": 5,
        "cyclomatic_complexity": 10
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_missing_both, schema=schema)

    # Case 4: Invalid record - missing required fields
    invalid_missing_required = {
        "task_id": "test-4",
        "cyclomatic_complexity": 10
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_missing_required, schema=schema)