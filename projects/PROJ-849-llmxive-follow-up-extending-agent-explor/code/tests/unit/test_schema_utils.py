"""
Utility functions for schema validation used across unit and contract tests.
Provides generic validators to ensure data structures match expected schemas.
"""
import pytest
from typing import List, Dict, Any, Callable, Optional


def validate_list_of_records(
    records: List[Dict[str, Any]],
    validator: Callable[[Dict[str, Any]], bool],
    record_type_name: str
) -> None:
    """
    Validates a list of records against a specific validator function.

    Args:
        records: List of dictionaries to validate.
        validator: Function that returns True if a record is valid.
        record_type_name: Human-readable name for error messages.

    Raises:
        ValueError: If validation fails for any record.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected a list of {record_type_name}, got {type(records)}")

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record at index {i} is not a dictionary")
        if not validator(record):
            raise ValueError(f"Record at index {i} failed validation for {record_type_name}")


def test_validate_list_of_records_valid() -> None:
    """Test that valid records pass validation."""
    def dummy_validator(record: Dict[str, Any]) -> bool:
        return "id" in record and isinstance(record["id"], str)

    valid_records = [
        {"id": "1", "data": "test1"},
        {"id": "2", "data": "test2"}
    ]
    validate_list_of_records(valid_records, dummy_validator, "test_records")
    # If no exception is raised, the test passes


def test_validate_list_of_records_invalid() -> None:
    """Test that invalid records raise ValueError."""
    def dummy_validator(record: Dict[str, Any]) -> bool:
        return "id" in record and isinstance(record["id"], str)

    invalid_records = [
        {"id": "1", "data": "test1"},
        {"data": "test2"}  # Missing 'id'
    ]

    with pytest.raises(ValueError, match="failed validation"):
        validate_list_of_records(invalid_records, dummy_validator, "test_records")
