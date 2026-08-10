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
    Contract test validating tasks.json schema against contracts/task.schema.yaml.
    """
    tasks_path = "data/raw/tasks.json"
    if not os.path.exists(tasks_path):
        pytest.skip(f"Tasks file not found: {tasks_path}. Run generate_data.py first.")

    with open(tasks_path, 'r') as f:
        data = json.load(f)

    schema = load_schema("task.schema.yaml")
    
    # Validate the root object structure
    errors = validate_against_schema(data, schema)
    
    assert len(errors) == 0, f"Schema validation failed for tasks.json: {errors}"

def test_skills_json_schema():
    """
    Contract test validating skills.json schema and overlap metrics against contracts/skill.schema.yaml.
    """
    skills_path = "data/raw/skills.json"
    if not os.path.exists(skills_path):
        pytest.skip(f"Skills file not found: {skills_path}. Run generate_data.py first.")

    with open(skills_path, 'r') as f:
        data = json.load(f)

    schema = load_schema("skill.schema.yaml")

    # Validate the root object structure
    errors = validate_against_schema(data, schema)
    
    assert len(errors) == 0, f"Schema validation failed for skills.json: {errors}"

    # Check overlap metrics in metadata
    if "metadata" in data:
        meta = data["metadata"]
        
        # Validate required metadata fields
        assert "mean_similarity" in meta, "Missing mean_similarity in metadata"
        assert "overlap_level" in meta, "Missing overlap_level in metadata"
        assert "maximal_overlap_detected" in meta, "Missing maximal_overlap_detected in metadata"
        assert "seed_used" in meta, "Missing seed_used in metadata"
        assert "total_skills" in meta, "Missing total_skills in metadata"
        
        # Type checks for metadata values
        assert isinstance(meta["mean_similarity"], (int, float)), "mean_similarity must be numeric"
        assert isinstance(meta["overlap_level"], str), "overlap_level must be string"
        assert isinstance(meta["maximal_overlap_detected"], bool), "maximal_overlap_detected must be boolean"
        assert isinstance(meta["total_skills"], int), "total_skills must be integer"
        
        # Validate consistency: if maximal_overlap_detected is True, mean_similarity should be high
        if meta["maximal_overlap_detected"]:
            assert meta["mean_similarity"] >= 0.95, \
                f"maximal_overlap_detected is True but mean_similarity ({meta['mean_similarity']}) < 0.95"
    else:
        pytest.fail("Missing 'metadata' key in skills.json")

    # Validate skills array content
    if "skills" in data and isinstance(data["skills"], list):
        assert len(data["skills"]) > 0, "Skills array is empty"
        
        # Check first skill for required fields
        first_skill = data["skills"][0]
        required_fields = ["id", "name", "code", "description", "embedding_dimension"]
        for field in required_fields:
            assert field in first_skill, f"Missing required field '{field}' in skills"
        
        # Check for uniqueness of IDs
        ids = [skill["id"] for skill in data["skills"]]
        assert len(ids) == len(set(ids)), "Skill IDs are not unique"
    else:
        pytest.fail("Missing or invalid 'skills' array in skills.json")