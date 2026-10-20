"""
Contract presence and minimal validation tests.

This test suite ensures that each root‑level contract schema file exists,
contains the mandatory top‑level keys ``properties`` and ``required``,
and that a minimal dummy instance validates against the schema.
"""

import os
import json
import yaml
import pytest
from jsonschema import validate, ValidationError

# Helper to locate a contract file relative to the repository root
def contract_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "contracts", filename)

# ----------------------------------------------------------------------
# Schema loading tests
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "schema_file,required_keys",
    [
        ("task.schema.yaml", ["properties", "required"]),
        ("skill.schema.yaml", ["properties", "required"]),
        ("experiment_log.schema.yaml", ["properties", "required"]),
        ("execution_log.schema.yaml", ["properties", "required"]),
        ("metrics.schema.yaml", ["properties", "required"]),
    ],
)
def test_schema_has_mandatory_keys(schema_file, required_keys):
    """Assert that each schema contains the mandatory top‑level keys."""
    path = contract_path(schema_file)
    assert os.path.exists(path), f"Schema file missing: {path}"
    with open(path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    for key in required_keys:
        assert key in schema, f"Key '{key}' not found in {schema_file}"

# ----------------------------------------------------------------------
# Minimal instance validation
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "schema_file,dummy_instance",
    [
        (
            "task.schema.yaml",
            {
                "task_id": "task_0",
                "description": "A dummy task description.",
                "ground_truth_path": ["skill_0"],
                "complexity": 1,
                "embedding_vector": [0.0],
            },
        ),
        (
            "skill.schema.yaml",
            {
                "skill_id": "S1",
                "function_code": "def dummy(): pass",
                "embedding_vector": [0.0],
                "usage_count": 0,
                "mean_cosine_similarity": 0.0,
            },
        ),
        (
            "experiment_log.schema.yaml",
            {
                "task_id": "task_0",
                "skill_id": "skill_0",
                "success": True,
                "latency": 0.0,
                "tokens": 0,
                "retrieval_precision": 0.0,
                "retrieval_diversity": 0.0,
                "pruning_risk_count": 0,
                "library_size": 10,
                "pruning_enabled": False,
                "edge_case": False,
            },
        ),
        (
            "execution_log.schema.yaml",
            {
                "log_id": "log_0",
                "task_id": "task_0",
                "library_size": 10,
                "pruning_enabled": False,
                "success": True,
                "failure_reason": "",
                "token_usage": 0,
                "latency_ms": 0.0,
                "retrieved_skill_ids": ["skill_0"],
                "timestamp": "2023-01-01T00:00:00Z",
            },
        ),
        (
            "metrics.schema.yaml",
            {
                "library_size": 10,
                "pruning_enabled": False,
                "total_tasks": 1,
                "success_rate": 1.0,
                "avg_latency_ms": 0.0,
                "precision_at_5": 1.0,
                "false_prune_count": 0,
                "breakpoint_estimate": 0.0,
            },
        ),
    ],
)
def test_dummy_instance_validates(schema_file, dummy_instance):
    """Validate a minimal dummy instance against each schema."""
    path = contract_path(schema_file)
    with open(path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    try:
        validate(instance=dummy_instance, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Dummy instance failed validation for {schema_file}: {e.message}")