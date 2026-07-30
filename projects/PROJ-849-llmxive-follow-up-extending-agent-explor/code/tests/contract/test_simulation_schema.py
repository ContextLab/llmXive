"""
Contract tests for the simulation data schema.
Validates the structure of simulated failure rate records.
"""
import pytest
from typing import Dict, Any, List


def validate_simulation_record(record: Dict[str, Any]) -> bool:
    """
    Validates a single simulation record.

    Expected schema:
    {
        "problem_id": str,
        "simulated_failure": bool,
        "failure_reason": str
    }
    """
    required_fields = {
        "problem_id": str,
        "simulated_failure": bool,
        "failure_reason": str
    }

    if not isinstance(record, dict):
        return False

    for field, expected_type in required_fields.items():
        if field not in record:
            return False
        if not isinstance(record[field], expected_type):
            return False

    return True


def test_simulation_output_schema_valid() -> None:
    """Test that a valid simulation record passes validation."""
    valid_record = {
        "problem_id": "math_001",
        "simulated_failure": True,
        "failure_reason": "Tool selection error"
    }
    assert validate_simulation_record(valid_record) is True


def test_simulation_output_schema_missing_field() -> None:
    """Test that a record with a missing field fails validation."""
    invalid_record = {
        "problem_id": "math_001",
        "simulated_failure": True
        # Missing "failure_reason"
    }
    assert validate_simulation_record(invalid_record) is False


def test_simulation_output_schema_wrong_type() -> None:
    """Test that a record with a wrong type fails validation."""
    invalid_record = {
        "problem_id": 123,  # Should be str
        "simulated_failure": True,
        "failure_reason": "Tool selection error"
    }
    assert validate_simulation_record(invalid_record) is False
