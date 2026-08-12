import json
import yaml
import jsonschema
import os
import pytest

def load_schema(schema_path):
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_tasks_json_schema():
    """Validate tasks.json against task.schema.yaml"""
    schema_path = "contracts/task.schema.yaml"
    data_path = "data/raw/tasks.json"
    
    assert os.path.exists(schema_path), f"Schema file not found: {schema_path}"
    assert os.path.exists(data_path), f"Data file not found: {data_path}"
    
    schema = load_schema(schema_path)
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Validate the 'tasks' list in the data
    tasks_list = data.get("tasks", [])
    assert len(tasks_list) > 0, "No tasks found in data"
    
    for task in tasks_list:
        try:
            jsonschema.validate(instance=task, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"Task validation failed: {e.message}")

def test_skills_json_schema():
    """Validate skills.json against skill.schema.yaml"""
    schema_path = "contracts/skill.schema.yaml"
    data_path = "data/raw/skills.json"
    
    assert os.path.exists(schema_path), f"Schema file not found: {schema_path}"
    assert os.path.exists(data_path), f"Data file not found: {data_path}"
    
    schema = load_schema(schema_path)
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Validate the 'skills' list in the data
    skills_list = data.get("skills", [])
    assert len(skills_list) > 0, "No skills found in data"
    
    for skill in skills_list:
        try:
            jsonschema.validate(instance=skill, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"Skill validation failed: {e.message}")