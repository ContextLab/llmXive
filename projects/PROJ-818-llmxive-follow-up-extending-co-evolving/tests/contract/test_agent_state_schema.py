"""
Contract tests for validating the 'agent_state' JSON structure.
Validates the state serialization of agents (Sequential, Mixed, Co-evolving).
"""
import json
import pytest
from typing import Any, Dict, List

# Schema definitions for validation
AGENT_STATE_SCHEMA = {
    "required_top_level": ["agent_type", "generation", "rule_evaluations", "population", "history"],
    "population_item_fields": ["id", "rule_set", "fitness_score", "age"],
    "history_item_fields": ["generation", "avg_fitness", "best_fitness", "rule_evaluations_count"],
    "coevolving_specific_fields": ["sub_populations", "exchange_history"]
}

def validate_dict_structure(data: Dict[str, Any], required_keys: List[str], context: str = "") -> None:
    """Validate that a dictionary contains all required keys."""
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise AssertionError(
            f"Validation failed for {context}: Missing required keys: {missing}. "
            f"Found keys: {list(data.keys())}"
        )

def validate_list_of_dicts(data_list: List[Dict[str, Any]], required_fields: List[str], item_name: str) -> None:
    """Validate that a list contains dictionaries with required fields."""
    if not isinstance(data_list, list):
        raise AssertionError(f"Validation failed: Expected a list for {item_name}, got {type(data_list)}")
    
    for idx, item in enumerate(data_list):
        if not isinstance(item, dict):
            raise AssertionError(f"Validation failed: Item {idx} in {item_name} is not a dict")
        
        missing = [k for k in required_fields if k not in item]
        if missing:
            raise AssertionError(
                f"Validation failed for {item_name}[{idx}]: Missing required fields: {missing}. "
                f"Found keys: {list(item.keys())}"
            )

def test_load_and_validate_agent_state_schema(tmp_path):
    """
    Contract test: Ensure a valid agent state JSON file passes schema validation.
    """
    valid_state = {
        "agent_type": "CoevolvingAgent",
        "generation": 10,
        "rule_evaluations": 5000,
        "population": [
            {"id": "pop_001", "rule_set": ["A", "B"], "fitness_score": 0.85, "age": 5},
            {"id": "pop_002", "rule_set": ["C", "D"], "fitness_score": 0.92, "age": 3}
        ],
        "history": [
            {"generation": 1, "avg_fitness": 0.5, "best_fitness": 0.6, "rule_evaluations_count": 100},
            {"generation": 10, "avg_fitness": 0.8, "best_fitness": 0.95, "rule_evaluations_count": 5000}
        ],
        "sub_populations": {"task_A": ["pop_001"], "task_B": ["pop_002"]},
        "exchange_history": [
            {"generation": 5, "source": "task_A", "target": "task_B", "rules": ["A"]}
        ]
    }

    # Write to temp file
    state_path = tmp_path / "valid_agent_state.json"
    with open(state_path, 'w') as f:
        json.dump(valid_state, f)

    # Load and validate
    with open(state_path, 'r') as f:
        data = json.load(f)

    # Top-level validation
    validate_dict_structure(data, AGENT_STATE_SCHEMA["required_top_level"], "agent_state root")
    
    # Population validation
    validate_list_of_dicts(data["population"], AGENT_STATE_SCHEMA["population_item_fields"], "population")
    
    # History validation
    validate_list_of_dicts(data["history"], AGENT_STATE_SCHEMA["history_item_fields"], "history")

    # Co-evolving specific validation
    if data["agent_type"] == "CoevolvingAgent":
        validate_dict_structure(data, ["sub_populations", "exchange_history"], "coevolving_state")

def test_invalid_agent_state_missing_generation(tmp_path):
    """
    Contract test: Ensure agent state missing 'generation' raises AssertionError.
    """
    invalid_state = {
        "agent_type": "SequentialAgent",
        "rule_evaluations": 100,
        "population": [],
        "history": []
        # Missing 'generation'
    }

    state_path = tmp_path / "invalid_state.json"
    with open(state_path, 'w') as f:
        json.dump(invalid_state, f)

    with open(state_path, 'r') as f:
        data = json.load(f)

    with pytest.raises(AssertionError) as exc_info:
        validate_dict_structure(data, AGENT_STATE_SCHEMA["required_top_level"], "agent_state root")
    
    assert "generation" in str(exc_info.value)
