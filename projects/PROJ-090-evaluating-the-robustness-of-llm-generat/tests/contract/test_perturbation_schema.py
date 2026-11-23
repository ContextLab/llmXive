"""
Contract test for perturbation output schema.

Verifies that the perturbation generation output matches the JSON schema
defined in contracts/perturbation_schema.json (v1.0).

Required fields:
- task_id (string)
- perturbation_type (string)
- raw_score (float)
- is_valid (boolean)
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List


def load_schema():
    """Load the perturbation schema from the contracts directory."""
    schema_path = Path("contracts/perturbation_schema.json")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_perturbation_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single perturbation record against the schema.
    
    Args:
        record: The perturbation record to validate.
        schema: The JSON schema definition.
        
    Returns:
        List of error messages. Empty if valid.
    """
    errors = []
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")
            continue
        
        # Type checking
        expected_type = properties.get(field, {}).get("type")
        value = record[field]
        
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Field '{field}' should be boolean, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"Field '{field}' should be array, got {type(value).__name__}")
    
    return errors


def test_perturbation_schema():
    """
    Contract test: Assert JSON schema matches v1.0 defined in contracts/perturbation_schema.json.
    
    This test verifies:
    1. The schema file exists and is valid JSON.
    2. The schema defines the required fields: task_id, perturbation_type, raw_score, is_valid.
    3. Sample records from the perturbation output conform to the schema.
    """
    # Load the schema
    schema = load_schema()
    
    # Verify schema version
    assert schema.get("schema_version") == "v1.0", "Schema version must be v1.0"
    
    # Verify required fields
    required_fields = schema.get("required", [])
    assert "task_id" in required_fields, "task_id is required"
    assert "perturbation_type" in required_fields, "perturbation_type is required"
    assert "raw_score" in required_fields, "raw_score is required"
    assert "is_valid" in required_fields, "is_valid is required"
    
    # Verify field types
    properties = schema.get("properties", {})
    assert properties.get("task_id", {}).get("type") == "string", "task_id must be string"
    assert properties.get("perturbation_type", {}).get("type") == "string", "perturbation_type must be string"
    assert properties.get("raw_score", {}).get("type") == "number", "raw_score must be number"
    assert properties.get("is_valid", {}).get("type") == "boolean", "is_valid must be boolean"
    
    # Load sample data if available (optional verification)
    candidates_path = Path("data/processed/perturbation_candidates.json")
    if candidates_path.exists():
        with open(candidates_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
        
        # Validate each record
        for i, record in enumerate(candidates):
            errors = validate_perturbation_record(record, schema)
            assert len(errors) == 0, f"Record {i} failed validation: {errors}"


if __name__ == "__main__":
    test_perturbation_schema()
    print("Contract test passed: perturbation schema is valid.")