import pytest
import json
import os
import yaml
from typing import Any, Dict, List

# Path to schemas
SCHEMAS_DIR = "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    path = os.path.join(SCHEMAS_DIR, schema_name)
    if not os.path.exists(path):
        pytest.fail(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data: Dict, schema: Dict, path: str = "") -> List[str]:
    """
    Simple recursive validator for JSON schema subset.
    Returns list of errors.
    """
    errors = []
    
    # Check type
    if "type" in schema:
        if not isinstance(data, schema["type"]):
            errors.append(f"{path}: Expected type {schema['type']}, got {type(data).__name__}")
            return errors # Cannot continue if type is wrong

    # Check properties for objects
    if schema.get("type") == "object" and "properties" in schema:
        for key, prop_schema in schema["properties"].items():
            if key in data:
                errors.extend(validate_against_schema(data[key], prop_schema, f"{path}.{key}"))
            elif "required" in schema and key in schema["required"]:
                errors.append(f"{path}: Missing required property '{key}'")

    # Check items for arrays
    if schema.get("type") == "array" and "items" in schema:
        if isinstance(data, list):
            for i, item in enumerate(data):
                errors.extend(validate_against_schema(item, schema["items"], f"{path}[{i}]"))

    return errors

def test_tasks_json_schema():
    """
    Contract test validating tasks.json schema.
    """
    tasks_path = "data/raw/tasks.json"
    if not os.path.exists(tasks_path):
        pytest.skip(f"Tasks file not found: {tasks_path}. Run generate_data.py first.")

    with open(tasks_path, 'r') as f:
        data = json.load(f)

    schema = load_schema("task.schema.yaml")
    
    # The root of tasks.json is an object with 'metadata' and 'tasks'
    # The schema might define the structure of the 'tasks' array or the whole file.
    # Assuming the schema defines the structure of the 'tasks' array items or the file root.
    # Based on T009, we need to validate the file structure.
    
    # Let's assume the schema defines the root object
    if "properties" in schema:
       # If schema expects root to be the object with metadata and tasks
       errors = validate_against_schema(data, schema)
    else:
       # If schema is for the array items
       if "tasks" in data:
           for i, task in enumerate(data["tasks"]):
               errors = validate_against_schema(task, schema, f"tasks[{i}]")
               if errors:
                   break
           else:
               errors = [] # Success
       else:
           errors = ["Missing 'tasks' key in data"]

    assert len(errors) == 0, f"Schema validation failed: {errors}"

def test_skills_json_schema():
    """
    Contract test validating skills.json schema and overlap metrics.
    """
    skills_path = "data/raw/skills.json"
    if not os.path.exists(skills_path):
        pytest.skip(f"Skills file not found: {skills_path}. Run generate_data.py first.")

    with open(skills_path, 'r') as f:
        data = json.load(f)

    schema = load_schema("skill.schema.yaml")

    # Similar logic as tasks
    if "properties" in schema:
       errors = validate_against_schema(data, schema)
    else:
       if "skills" in data:
           for i, skill in enumerate(data["skills"]):
               errors = validate_against_schema(skill, schema, f"skills[{i}]")
               if errors:
                   break
           else:
               errors = []
       else:
           errors = ["Missing 'skills' key in data"]

    assert len(errors) == 0, f"Schema validation failed: {errors}"

    # Check overlap metrics in metadata
    if "metadata" in data:
        meta = data["metadata"]
        assert "mean_similarity" in meta, "Missing mean_similarity in metadata"
        assert "overlap_level" in meta, "Missing overlap_level in metadata"
        assert "maximal_overlap_detected" in meta, "Missing maximal_overlap_detected in metadata"
    else:
        pytest.fail("Missing 'metadata' key in skills.json")