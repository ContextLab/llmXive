"""
Contract tests for agent state schema validation.
Validates the structure of saved agent states (rule sets, performance metrics).
"""
import json
import os
import pytest
from typing import Any, Dict, List

AGENT_STATE_SCHEMA = {
    "required_keys": ["agent_id", "condition", "generation", "rule_set", "metrics"],
    "rule_set_keys": ["rules", "score", "history"],
    "metrics_keys": ["accuracy", "evaluations", "forgetting_rate"],
    "conditions": ["sequential", "mixed", "coevolving"]
}

def validate_agent_state_structure(data: Dict[str, Any]) -> List[str]:
    """
    Validates an agent state dictionary against the expected schema.
    Returns a list of validation errors (empty if valid).
    """
    errors = []

    # Check top-level required keys
    for key in AGENT_STATE_SCHEMA["required_keys"]:
        if key not in data:
            errors.append(f"Missing required top-level key: {key}")

    # Validate condition
    if "condition" in data and data["condition"] not in AGENT_STATE_SCHEMA["conditions"]:
        errors.append(f"Invalid condition: {data['condition']}")

    # Validate rule_set structure
    if "rule_set" in data:
        rs = data["rule_set"]
        for key in AGENT_STATE_SCHEMA["rule_set_keys"]:
            if key not in rs:
                errors.append(f"Missing required rule_set key: {key}")
        
        if "rules" in rs and not isinstance(rs["rules"], list):
            errors.append("'rule_set.rules' must be a list")

    # Validate metrics structure
    if "metrics" in data:
        metrics = data["metrics"]
        for key in AGENT_STATE_SCHEMA["metrics_keys"]:
            if key not in metrics:
                errors.append(f"Missing required metrics key: {key}")
        
        # Check numeric types
        if "accuracy" in metrics and not isinstance(metrics["accuracy"], (int, float)):
            errors.append("'metrics.accuracy' must be a number")

    return errors

def load_agent_state(filepath: str) -> Dict[str, Any]:
    """Load an agent state from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Agent state file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

@pytest.mark.contract
def test_sequential_agent_state_schema():
    """Test that a sequential agent state conforms to the schema."""
    try:
        state = load_agent_state("data/results/agent_sequential_state.json")
        errors = validate_agent_state_structure(state)
        assert len(errors) == 0, f"Schema validation failed: {errors}"
    except FileNotFoundError:
        pytest.skip("Agent state file not found. Run training tasks first.")

@pytest.mark.contract
def test_mixed_agent_state_schema():
    """Test that a mixed agent state conforms to the schema."""
    try:
        state = load_agent_state("data/results/agent_mixed_state.json")
        errors = validate_agent_state_structure(state)
        assert len(errors) == 0, f"Schema validation failed: {errors}"
    except FileNotFoundError:
        pytest.skip("Agent state file not found. Run training tasks first.")

@pytest.mark.contract
def test_coevolving_agent_state_schema():
    """Test that a co-evolving agent state conforms to the schema."""
    try:
        state = load_agent_state("data/results/agent_coevolving_state.json")
        errors = validate_agent_state_structure(state)
        assert len(errors) == 0, f"Schema validation failed: {errors}"
    except FileNotFoundError:
        pytest.skip("Agent state file not found. Run training tasks first.")
