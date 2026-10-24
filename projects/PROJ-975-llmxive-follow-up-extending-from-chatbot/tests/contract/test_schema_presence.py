import json
import yaml
import os
from jsonschema import validate, ValidationError

# Paths to contract schemas
CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "contracts")

def load_schema(name):
    schema_path = os.path.join(CONTRACTS_DIR, f"{name}.schema.yaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_presence():
    # Ensure each contract file exists and has required top‑level keys
    for schema_name in ["task", "skill", "experiment_log", "execution_log", "metrics"]:
        schema = load_schema(schema_name)
        assert "properties" in schema, f"{schema_name} schema missing 'properties'"
        assert "required" in schema, f"{schema_name} schema missing 'required'"

def test_dummy_instance_validation():
    # Minimal dummy instances that satisfy each schema
    task_schema = load_schema("task")
    skill_schema = load_schema("skill")
    # Build dummy objects
    dummy_task = {
        "task_id": "task_0000",
        "description": "Dummy description",
        "ground_truth_path": ["skill_001"],
        "complexity": 1,
        "embedding_vector": [0.0] * 384,
        "edge_case": False,
    }
    dummy_skill = {
        "skill_id": "skill_001",
        "function_code": "def dummy(): pass",
        "embedding_vector": [0.0] * 384,
        "usage_count": 0,
    }
    # Validate
    validate(instance=dummy_task, schema=task_schema)
    validate(instance=dummy_skill, schema=skill_schema)