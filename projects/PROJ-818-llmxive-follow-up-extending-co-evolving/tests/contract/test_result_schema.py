"""
Contract tests for validating the 'result' JSON structure.
Validates the output structure after training and evaluation, including forgetting metrics.
"""
import json
import pytest
from typing import Any, Dict, List

# Schema definitions for validation
RESULT_SCHEMA = {
    "required_top_level": ["run_id", "condition", "seed", "training_stats", "evaluation_results", "forgetting_metrics"],
    "training_stats_fields": ["total_generations", "total_rule_evaluations", "final_fitness", "duration_seconds"],
    "evaluation_result_fields": ["task_type", "task_id", "accuracy", "rules_retained"],
    "forgetting_metrics_fields": ["initial_accuracy", "final_accuracy", "accuracy_drop", "retention_rate"],
    "condition_values": ["sequential", "mixed", "coevolving"]
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

def test_load_and_validate_result_schema(tmp_path):
    """
    Contract test: Ensure a valid result JSON file passes schema validation.
    """
    valid_result = {
        "run_id": "run_001",
        "condition": "coevolving",
        "seed": 42,
        "training_stats": {
            "total_generations": 100,
            "total_rule_evaluations": 10000,
            "final_fitness": 0.95,
            "duration_seconds": 120.5
        },
        "evaluation_results": [
            {"task_type": "logic", "task_id": "proof_001", "accuracy": 0.9, "rules_retained": ["Modus Ponens"]},
            {"task_type": "grid", "task_id": "grid_001", "accuracy": 0.85, "rules_retained": ["avoid_red"]}
        ],
        "forgetting_metrics": {
            "initial_accuracy": 0.98,
            "final_accuracy": 0.88,
            "accuracy_drop": 0.10,
            "retention_rate": 0.90
        }
    }

    # Write to temp file
    result_path = tmp_path / "valid_result.json"
    with open(result_path, 'w') as f:
        json.dump(valid_result, f)

    # Load and validate
    with open(result_path, 'r') as f:
        data = json.load(f)

    # Top-level validation
    validate_dict_structure(data, RESULT_SCHEMA["required_top_level"], "result root")
    
    # Training stats validation
    validate_dict_structure(data["training_stats"], RESULT_SCHEMA["training_stats_fields"], "training_stats")
    
    # Evaluation results validation
    validate_list_of_dicts(data["evaluation_results"], RESULT_SCHEMA["evaluation_result_fields"], "evaluation_results")
    
    # Forgetting metrics validation
    validate_dict_structure(data["forgetting_metrics"], RESULT_SCHEMA["forgetting_metrics_fields"], "forgetting_metrics")

    # Condition validation
    assert data["condition"] in RESULT_SCHEMA["condition_values"], f"Invalid condition: {data['condition']}"

def test_invalid_result_missing_forgetting_metrics(tmp_path):
    """
    Contract test: Ensure result missing 'forgetting_metrics' raises AssertionError.
    """
    invalid_result = {
        "run_id": "run_002",
        "condition": "sequential",
        "seed": 43,
        "training_stats": {"total_generations": 10, "total_rule_evaluations": 100, "final_fitness": 0.5, "duration_seconds": 10.0},
        "evaluation_results": []
        # Missing 'forgetting_metrics'
    }

    result_path = tmp_path / "invalid_result.json"
    with open(result_path, 'w') as f:
        json.dump(invalid_result, f)

    with open(result_path, 'r') as f:
        data = json.load(f)

    with pytest.raises(AssertionError) as exc_info:
        validate_dict_structure(data, RESULT_SCHEMA["required_top_level"], "result root")
    
    assert "forgetting_metrics" in str(exc_info.value)
