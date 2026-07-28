"""
Contract tests for validating the 'parity' JSON structure.
Validates that rule evaluation counts match across different training conditions.
"""
import json
import pytest
from typing import Any, Dict, List

# Schema definitions for validation
PARITY_SCHEMA = {
    "required_top_level": ["conditions", "reference_count", "status"],
    "condition_entry_fields": ["condition_name", "total_evaluations", "checksum"],
    "status_values": ["PASS", "FAIL", "WARNING"]
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

def test_load_and_validate_parity_schema(tmp_path):
    """
    Contract test: Ensure a valid parity check JSON file passes schema validation.
    """
    valid_parity = {
        "conditions": [
            {"condition_name": "sequential", "total_evaluations": 10000, "checksum": "abc123..."},
            {"condition_name": "mixed", "total_evaluations": 10000, "checksum": "def456..."},
            {"condition_name": "coevolving", "total_evaluations": 10000, "checksum": "ghi789..."}
        ],
        "reference_count": 10000,
        "status": "PASS"
    }

    # Write to temp file
    parity_path = tmp_path / "valid_parity.json"
    with open(parity_path, 'w') as f:
        json.dump(valid_parity, f)

    # Load and validate
    with open(parity_path, 'r') as f:
        data = json.load(f)

    # Top-level validation
    validate_dict_structure(data, PARITY_SCHEMA["required_top_level"], "parity root")
    
    # Conditions validation
    validate_list_of_dicts(data["conditions"], PARITY_SCHEMA["condition_entry_fields"], "conditions")
    
    # Status validation
    assert data["status"] in PARITY_SCHEMA["status_values"], f"Invalid status: {data['status']}"

def test_invalid_parity_missing_reference_count(tmp_path):
    """
    Contract test: Ensure parity missing 'reference_count' raises AssertionError.
    """
    invalid_parity = {
        "conditions": [
            {"condition_name": "sequential", "total_evaluations": 10000, "checksum": "abc123..."}
        ],
        "status": "PASS"
        # Missing 'reference_count'
    }

    parity_path = tmp_path / "invalid_parity.json"
    with open(parity_path, 'w') as f:
        json.dump(invalid_parity, f)

    with open(parity_path, 'r') as f:
        data = json.load(f)

    with pytest.raises(AssertionError) as exc_info:
        validate_dict_structure(data, PARITY_SCHEMA["required_top_level"], "parity root")
    
    assert "reference_count" in str(exc_info.value)