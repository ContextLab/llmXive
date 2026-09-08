"""
Integration test to ensure all schemas can be loaded and basic validation flows work.
"""
import json
import pytest
from tests.contract.schemas import (
    DATASET_SCHEMA, AGENT_STATE_SCHEMA, RESULT_SCHEMA,
    validate_dataset, validate_agent_state, validate_result
)

def test_schemas_are_valid_json():
    """Ensure the schema definitions are valid JSON structures."""
    assert isinstance(DATASET_SCHEMA, dict)
    assert isinstance(AGENT_STATE_SCHEMA, dict)
    assert isinstance(RESULT_SCHEMA, dict)
    assert "$schema" in DATASET_SCHEMA
    assert "$schema" in AGENT_STATE_SCHEMA
    assert "$schema" in RESULT_SCHEMA

def test_round_trip_serialization():
    """Test that valid data can be serialized and deserialized and still pass validation."""
    data = {
        "metadata": {"version": "1.0", "seed": 1, "generator": "Test", "timestamp": "2023-01-01T00:00:00Z", "checksum": "x"},
        "data": [{"type": "logic_proof", "id": "p1", "axioms": ["A"], "conclusion": "B", "proof_steps": []}]
    }
    json_str = json.dumps(data)
    loaded_data = json.loads(json_str)
    result = validate_dataset(loaded_data)
    assert result.valid

    state = {
        "agent_type": "TestAgent",
        "config": {},
        "population": [{"id": "r1", "rules": [], "fitness": 1.0}],
        "evaluation_stats": {"total_evaluations": 1, "by_task": {}}
    }
    json_str = json.dumps(state)
    loaded_state = json.loads(json_str)
    result = validate_agent_state(loaded_state)
    assert result.valid

    res = {
        "run_id": "r1",
        "condition": "sequential",
        "metrics": {"initial_accuracy": 1.0, "final_accuracy": 1.0, "forgetting_rate": 0.0},
        "parity_data": {"total_evaluations": 1, "checksum": "x"}
    }
    json_str = json.dumps(res)
    loaded_res = json.loads(json_str)
    result = validate_result(loaded_res)
    assert result.valid