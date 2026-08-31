"""
Contract test for T009a: Validate tasks.json schema against contracts/task.schema.yaml.

This test verifies that the JSON schema defined in contracts/task.schema.yaml
correctly validates sample task objects.
"""
import json
import os
import yaml
import pytest
from jsonschema import validate, ValidationError

# Resolve paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "contracts", "task.schema.yaml")
SAMPLE_TASK = {
    "task_id": "T001",
    "description": "Create subdirectories for project structure",
    "ground_truth_path": "data/raw/sample_task.json",
    "complexity": "low"
}

def load_schema():
    """Load the YAML schema file."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_loads():
    """Verify the schema file is valid YAML and loads correctly."""
    schema = load_schema()
    assert schema is not None
    assert "$schema" in schema
    assert schema["title"] == "Task Schema"

def test_valid_task_passes_validation():
    """Verify that a valid task object passes jsonschema.validate."""
    schema = load_schema()
    try:
        validate(instance=SAMPLE_TASK, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid task failed validation: {e.message}")

def test_missing_required_field_fails():
    """Verify that a task missing a required field fails validation."""
    schema = load_schema()
    invalid_task = SAMPLE_TASK.copy()
    del invalid_task["task_id"]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=schema)

def test_invalid_complexity_fails():
    """Verify that a task with invalid complexity value fails validation."""
    schema = load_schema()
    invalid_task = SAMPLE_TASK.copy()
    invalid_task["complexity"] = "super_hard"
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=schema)

def test_invalid_task_id_format_fails():
    """Verify that a task with invalid task_id format fails validation."""
    schema = load_schema()
    invalid_task = SAMPLE_TASK.copy()
    invalid_task["task_id"] = "INVALID_ID"
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=schema)

def test_extra_properties_fails():
    """Verify that a task with extra properties fails validation (additionalProperties: false)."""
    schema = load_schema()
    invalid_task = SAMPLE_TASK.copy()
    invalid_task["unknown_field"] = "should not be allowed"
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=schema)

def test_metadata_field_is_optional():
    """Verify that a task without metadata field passes validation."""
    schema = load_schema()
    task_without_metadata = {
        "task_id": "T002",
        "description": "Another task",
        "ground_truth_path": "data/raw/another.json",
        "complexity": "medium"
    }
    try:
        validate(instance=task_without_metadata, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Task without metadata failed validation: {e.message}")