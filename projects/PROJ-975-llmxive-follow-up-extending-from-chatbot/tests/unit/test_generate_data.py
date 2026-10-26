import json
import os
import sys
import pathlib
import pytest
import numpy as np
from jsonschema import validate

# Ensure the code directory is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_data import (
    generate_skills,
    generate_tasks,
    validate_similarity_thresholds,
    SKILL_COUNT,
    TASK_COUNT,
)
from llmxive_toolkit import paths

def load_yaml_schema(name):
    import yaml
    path = paths.path("contracts", f"{name}.schema.yaml")
    if not path.exists():
        pytest.skip(f"Schema {path} not found.")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def test_skill_generation_deterministic():
    seed = 42
    assert generate_skills(seed, count=10) == generate_skills(seed, count=10)

def test_task_generation_deterministic():
    seed = 42
    skills = generate_skills(seed, count=10)
    assert generate_tasks(seed, skills, count=20) == generate_tasks(seed, skills, count=20)

def test_counts():
    skills = generate_skills(42, count=SKILL_COUNT)
    tasks = generate_tasks(123, skills, count=TASK_COUNT)
    assert len(skills) == SKILL_COUNT
    assert len(tasks) == TASK_COUNT

def test_schema_compliance():
    # This test requires the files to be generated first
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    
    if not tasks_path.exists() or not skills_path.exists():
        pytest.skip("Data files not found. Run generate_data.py first.")

    with open(tasks_path, 'r') as f:
        tasks_data = json.load(f)['tasks']
    with open(skills_path, 'r') as f:
        skills_data = json.load(f)['skills']

    task_schema = load_yaml_schema("task")
    skill_schema = load_yaml_schema("skill")

    for t in tasks_data:
        validate(instance=t, schema=task_schema)
    for s in skills_data:
        validate(instance=s, schema=skill_schema)

def test_overlap_thresholds():
    # Test High
    skills_high = generate_skills(42, count=20, overlap_level="high")
    assert validate_similarity_thresholds(skills_high, "high")["is_valid"]
    # Test Low
    skills_low = generate_skills(42, count=20, overlap_level="low")
    assert validate_similarity_thresholds(skills_low, "low")["is_valid"]

def test_checksums():
    checksums_path = paths.data("raw", "checksums.json")
    if not checksums_path.exists():
        pytest.skip("Checksum file not found.")
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    import hashlib
    def get_sha(p):
        sha = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    assert checksums["tasks_json_sha256"] == get_sha(paths.data("raw", "tasks.json"))
    assert checksums["skills_json_sha256"] == get_sha(paths.data("raw", "skills.json"))