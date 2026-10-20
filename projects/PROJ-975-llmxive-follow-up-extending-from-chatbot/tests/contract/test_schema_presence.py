import json
import yaml
import hashlib
from jsonschema import validate, ValidationError
from pathlib import Path

# Paths to the root-level contract schemas
CONTRACTS_DIR = Path("contracts")

SCHEMAS = {
    "task": CONTRACTS_DIR / "task.schema.yaml",
    "skill": CONTRACTS_DIR / "skill.schema.yaml",
    "experiment_log": CONTRACTS_DIR / "experiment_log.schema.yaml",
    "execution_log": CONTRACTS_DIR / "execution_log.schema.yaml",
    "metrics": CONTRACTS_DIR / "metrics.schema.yaml",
}

def load_schema(name):
    with open(SCHEMAS[name], "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_presence():
    for name, path in SCHEMAS.items():
        assert path.exists(), f"Schema file {path} does not exist"
        schema = load_schema(name)
        assert "properties" in schema, f"{name} schema missing 'properties'"
        assert "required" in schema, f"{name} schema missing 'required'"

def test_dummy_instance_validation():
    # Minimal dummy instances that satisfy each schema
    task_instance = {
        "task_id": "task_001",
        "description": "Dummy task description",
        "ground_truth_path": ["skill_001"],
        "complexity": 1,
        "embedding_vector": [0.0] * 768,
    }
    skill_instance = {
        "skill_id": "skill_001",
        "function_code": "def dummy(): pass",
        "embedding_vector": [0.0] * 768,
        "usage_count": 0,
    }

    # Validate task
    task_schema = load_schema("task")
    validate(task_instance, task_schema)

    # Validate skill
    skill_schema = load_schema("skill")
    validate(skill_instance, skill_schema)