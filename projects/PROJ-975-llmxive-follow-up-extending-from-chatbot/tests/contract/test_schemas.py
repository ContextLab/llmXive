"""
tests/contract/test_schemas.py

Contract tests validating tasks.json and skills.json against their respective schemas.
"""
import pytest
import json
import os
import sys
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

SCHEMAS_DIR = "contracts"
TASK_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "task.schema.yaml")
SKILL_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "skill.schema.yaml")
TASKS_JSON_PATH = "data/raw/tasks.json"
SKILLS_JSON_PATH = "data/raw/skills.json"

def load_schema(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_task_schema(task: dict, schema: dict):
    """Validates a single task object against the task schema."""
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for field in required_fields:
        if field not in task:
            raise AssertionError(f"Missing required field: {field}")
    
    for field, value in task.items():
        if field in properties:
            expected_type = properties[field].get("type")
            if expected_type == "integer" and not isinstance(value, int):
                raise AssertionError(f"Field {field} should be integer, got {type(value)}")
            elif expected_type == "array" and not isinstance(value, list):
                raise AssertionError(f"Field {field} should be array, got {type(value)}")
            elif expected_type == "string" and not isinstance(value, str):
                raise AssertionError(f"Field {field} should be string, got {type(value)}")

def validate_skill_schema(skill: dict, schema: dict):
    """Validates a single skill object against the skill schema."""
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for field in required_fields:
        if field not in skill:
            raise AssertionError(f"Missing required field: {field}")
    
    for field, value in skill.items():
        if field in properties:
            expected_type = properties[field].get("type")
            if expected_type == "string" and not isinstance(value, str):
                raise AssertionError(f"Field {field} should be string, got {type(value)}")

@pytest.fixture
def task_schema():
    return load_schema(TASK_SCHEMA_PATH)

@pytest.fixture
def skill_schema():
    return load_schema(SKILL_SCHEMA_PATH)

@pytest.fixture
def tasks_data():
    if not os.path.exists(TASKS_JSON_PATH):
        pytest.skip(f"Tasks file not found: {TASKS_JSON_PATH}")
    with open(TASKS_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def skills_data():
    if not os.path.exists(SKILLS_JSON_PATH):
        pytest.skip(f"Skills file not found: {SKILLS_JSON_PATH}")
    with open(SKILLS_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_tasks_schema_structure(tasks_data, task_schema):
    """Validates the structure of tasks.json against task.schema.yaml"""
    assert "tasks" in tasks_data, "Root 'tasks' key missing"
    assert "metadata" in tasks_data, "Root 'metadata' key missing"
    
    tasks = tasks_data["tasks"]
    assert isinstance(tasks, list), "Tasks should be a list"
    assert len(tasks) > 0, "Tasks list is empty"
    
    # Validate each task
    for i, task in enumerate(tasks):
        validate_task_schema(task, task_schema)

def test_skills_schema_structure(skills_data, skill_schema):
    """Validates the structure of skills.json against skill.schema.yaml"""
    assert "skills" in skills_data, "Root 'skills' key missing"
    assert "metadata" in skills_data, "Root 'metadata' key missing"
    
    skills = skills_data["skills"]
    assert isinstance(skills, list), "Skills should be a list"
    assert len(skills) > 0, "Skills list is empty"
    
    # Validate each skill
    for i, skill in enumerate(skills):
        validate_skill_schema(skill, skill_schema)

def test_tasks_count(tasks_data):
    """Validates that exactly 500 tasks are generated."""
    assert len(tasks_data["tasks"]) == 500, f"Expected 500 tasks, got {len(tasks_data['tasks'])}"

def test_skills_count(skills_data):
    """Validates that exactly 100 skills are generated."""
    assert len(skills_data["skills"]) == 100, f"Expected 100 skills, got {len(skills_data['skills'])}"

def test_ground_truth_path_validity(tasks_data):
    """Validates that ground-truth paths are lists of 3-5 unique skill IDs."""
    skill_ids = {s["id"] for s in skills_data["skills"]}
    
    for task in tasks_data["tasks"]:
        path = task.get("ground_truth_path", [])
        assert isinstance(path, list), "ground_truth_path must be a list"
        assert 3 <= len(path) <= 5, f"Path length must be 3-5, got {len(path)}"
        assert len(path) == len(set(path)), "Path must contain unique skill IDs"
        for sid in path:
            assert sid in skill_ids, f"Skill ID {sid} in path not found in skills"
