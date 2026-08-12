import json
import yaml
import jsonschema
import os
import pytest

def test_task_schema_validation():
    """Validate that a sample task object passes against task.schema.yaml."""
    # Load the schema
    schema_path = os.path.join("contracts", "task.schema.yaml")
    assert os.path.exists(schema_path), f"Schema file not found at {schema_path}"
    
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    # Define a valid sample task object
    sample_task = {
        "task_id": "T009a",
        "description": "Create task schema definition",
        "ground_truth_path": "data/raw/tasks.json",
        "complexity": "medium"
    }

    # Validate the sample object
    try:
        jsonschema.validate(instance=sample_task, schema=schema)
        assert True, "Schema validation passed"
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")

def test_task_schema_invalid_task_id():
    """Ensure invalid task_id format raises validation error."""
    schema_path = os.path.join("contracts", "task.schema.yaml")
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    invalid_task = {
        "task_id": "INVALID-ID",
        "description": "Test invalid ID",
        "ground_truth_path": "data/raw/test.json",
        "complexity": "low"
    }

    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(instance=invalid_task, schema=schema)

def test_task_schema_missing_required_field():
    """Ensure missing required field raises validation error."""
    schema_path = os.path.join("contracts", "task.schema.yaml")
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    incomplete_task = {
        "task_id": "T009a",
        "description": "Missing ground_truth_path"
    }

    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(instance=incomplete_task, schema=schema)