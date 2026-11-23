"""
Contract test for T009c: Validates that experiment log entries conform to the schema.
"""
import os
import sys
import yaml
import pytest
from jsonschema import validate, ValidationError

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

SCHEMA_PATH = os.path.join("contracts", "experiment_log.schema.yaml")

@pytest.fixture
def schema():
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_valid_log_entry(schema):
    """Test that a valid log entry passes validation."""
    valid_entry = {
        "run_id": "run_10_off_LOW",
        "task_id": "T001",
        "library_size": 10,
        "pruning_enabled": False,
        "success": True,
        "latency_ms": 1.23,
        "tokens_used": 0,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 0.9,
        "edge_case": "none"
    }
    validate(instance=valid_entry, schema=schema)

def test_edge_case_entry(schema):
    """Test that an edge case entry (maximal overlap) passes validation."""
    edge_entry = {
        "run_id": "run_20_fr04_HIGH",
        "task_id": "T099",
        "library_size": 20,
        "pruning_enabled": True,
        "success": False,
        "latency_ms": 2.5,
        "tokens_used": 0,
        "retrieval_precision": 0.0,
        "retrieval_diversity": 0.0,
        "edge_case": "maximal_overlap"
    }
    validate(instance=edge_entry, schema=schema)