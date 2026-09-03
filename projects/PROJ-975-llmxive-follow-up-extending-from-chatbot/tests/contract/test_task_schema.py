"""
Contract test for T009a: Validate tasks.json against contracts/task.schema.yaml.
"""
import json
import os
import yaml
import pytest
from jsonschema import validate, ValidationError

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'contracts', 'task.schema.yaml')
TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'tasks.json')

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def tasks_data():
    if not os.path.exists(TASKS_PATH):
        pytest.skip(f"Tasks file not found at {TASKS_PATH}. Run generate_data.py first.")
    with open(TASKS_PATH, 'r') as f:
        data = json.load(f)
    # Handle if data is a list or a dict with a 'tasks' key
    if isinstance(data, dict) and 'tasks' in data:
        return data['tasks']
    return data

def test_schema_loads(schema):
    """Ensure the YAML schema is valid and loads correctly."""
    assert 'properties' in schema
    assert 'task_id' in schema['properties']
    assert 'description' in schema['properties']
    assert 'ground_truth_path' in schema['properties']
    assert 'complexity' in schema['properties']

def test_sample_task_validates(schema):
    """Validate a single sample task object against the schema."""
    sample_task = {
        "task_id": "TASK_SAMPLE_001",
        "description": "Calculate the sum of two numbers and return the result.",
        "ground_truth_path": ["skill_add", "skill_return"],
        "complexity": 2
    }
    try:
        validate(instance=sample_task, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Sample task failed schema validation: {e.message}")

def test_all_tasks_validate(schema, tasks_data):
    """Validate every task in the generated dataset against the schema."""
    assert len(tasks_data) > 0, "No tasks found to validate."
    
    errors = []
    for idx, task in enumerate(tasks_data):
        try:
            validate(instance=task, schema=schema)
        except ValidationError as e:
            errors.append(f"Task {idx} (ID: {task.get('task_id', 'UNKNOWN')}): {e.message}")
    
    if errors:
        pytest.fail(f"Schema validation failed for {len(errors)} tasks:\n" + "\n".join(errors[:5]))