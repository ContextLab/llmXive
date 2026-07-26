import pytest
from typing import Dict, Any, List

def validate_simulation_record(record: Dict[str, Any]) -> bool:
    """Validate a single simulation record schema."""
    required_fields = ["problem_id", "simulated_failure", "failure_reason"]
    
    for field in required_fields:
        if field not in record:
            return False
    
    if not isinstance(record["problem_id"], str):
        return False
    if not isinstance(record["simulated_failure"], bool):
        return False
    if not isinstance(record["failure_reason"], str):
        return False
        
    return True

def test_simulation_output_schema_valid():
    """Test a valid simulation record."""
    sample = {
        "problem_id": "test-123",
        "simulated_failure": True,
        "failure_reason": "Tool mismatch"
    }
    assert validate_simulation_record(sample) is True

def test_simulation_output_schema_missing_field():
    """Test missing field."""
    sample = {
        "problem_id": "test-123",
        "simulated_failure": True
        # Missing failure_reason
    }
    assert validate_simulation_record(sample) is False

def test_simulation_output_schema_wrong_type():
    """Test wrong type."""
    sample = {
        "problem_id": "test-123",
        "simulated_failure": "yes",  # Should be bool
        "failure_reason": "Tool mismatch"
    }
    assert validate_simulation_record(sample) is False

def test_simulation_output_schema_empty_record():
    """Test empty record."""
    sample = {}
    assert validate_simulation_record(sample) is False
