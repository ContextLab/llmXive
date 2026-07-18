"""
Contract test for intake survey schema (US2).

This test verifies that the covariate collection logic in
`code/data_collection_interface.py` produces output conforming to the
required schema defined in the project specifications (FR-003).

Schema Requirements:
- participant_id: string (UUID)
- INCOM_score: non-negative number
- usage_frequency: non-negative number (hours/week)
- timestamp: ISO 8601 string
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path to import sibling modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data_collection_interface import collect_covariates, get_input


def test_intake_schema_structure():
    """
    Contract test: Verify the output dictionary of collect_covariates
    contains exactly the required keys with correct types.
    """
    # Mock inputs to simulate a valid participant session
    # We patch get_input to return deterministic values instead of reading stdin
    mock_responses = {
        "incom_prompt": 15.0,
        "usage_prompt": 10.5
    }

    def mock_get_input(prompt: str, value_type: str = "float", min_val: float = None, max_val: float = None) -> float:
        if "INCOM" in prompt:
            return mock_responses["incom_prompt"]
        elif "usage" in prompt or "hours" in prompt:
            return mock_responses["usage_prompt"]
        return 0.0

    # Patch the function temporarily
    original_get_input = None
    # Since get_input is imported at module level in data_collection_interface,
    # we need to patch it where it's used.
    import data_collection_interface
    original_get_input = data_collection_interface.get_input
    data_collection_interface.get_input = mock_get_input

    try:
        # Run the collection logic
        # We pass a dummy session_id to ensure a file isn't written or we handle it
        # The function signature expects a session_id and returns the data dict
        result = collect_covariates("test_session_001")

        # Assert schema keys exist
        required_keys = {
            "participant_id",
            "INCOM_score",
            "usage_frequency",
            "timestamp"
        }
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - set(result.keys())}"

        # Assert types
        assert isinstance(result["participant_id"], str), "participant_id must be a string"
        assert isinstance(result["INCOM_score"], (int, float)), "INCOM_score must be a number"
        assert isinstance(result["usage_frequency"], (int, float)), "usage_frequency must be a number"
        assert isinstance(result["timestamp"], str), "timestamp must be a string"

        # Assert value constraints (non-negative)
        assert result["INCOM_score"] >= 0, "INCOM_score must be non-negative"
        assert result["usage_frequency"] >= 0, "usage_frequency must be non-negative"

        # Assert specific values match our mock
        assert result["INCOM_score"] == 15.0, "INCOM_score mismatch"
        assert result["usage_frequency"] == 10.5, "usage_frequency mismatch"

    finally:
        # Restore original function
        data_collection_interface.get_input = original_get_input


def test_intake_schema_validation_rejection():
    """
    Contract test: Verify that invalid inputs (negative values) raise
    a ValueError or similar, ensuring the schema contract is enforced.
    """
    def mock_negative_input(prompt: str, value_type: str = "float", min_val: float = None, max_val: float = None) -> float:
        # Return a negative value to test validation logic
        return -5.0

    import data_collection_interface
    original_get_input = data_collection_interface.get_input
    data_collection_interface.get_input = mock_negative_input

    try:
        # The collect_covariates function should handle validation internally
        # or raise an error if min_val checks fail.
        # Based on the spec, we expect the system to reject negative inputs.
        # If the implementation loops until valid, this test would hang.
        # We assume the implementation raises ValueError on invalid range.
        try:
            result = collect_covariates("test_session_reject")
            # If we get here, check if it enforced the constraint
            # (Some implementations might just warn, but spec says "non-negative range")
            # For this contract test, we assert that valid data is not produced with negative values
            assert result["INCOM_score"] >= 0, "System accepted negative INCOM score"
        except ValueError:
            # Expected behavior: rejection of invalid input
            pass
    finally:
        data_collection_interface.get_input = original_get_input


def test_intake_schema_json_serializability():
    """
    Contract test: Ensure the output dictionary can be serialized to JSON.
    This is critical for writing to .jsonl files.
    """
    mock_responses = {
        "incom_prompt": 20.0,
        "usage_prompt": 5.0
    }

    def mock_get_input(prompt: str, value_type: str = "float", min_val: float = None, max_val: float = None) -> float:
        if "INCOM" in prompt:
            return mock_responses["incom_prompt"]
        elif "usage" in prompt or "hours" in prompt:
            return mock_responses["usage_prompt"]
        return 0.0

    import data_collection_interface
    original_get_input = data_collection_interface.get_input
    data_collection_interface.get_input = mock_get_input

    try:
        result = collect_covariates("test_session_json")

        # Attempt serialization
        json_str = json.dumps(result)
        assert len(json_str) > 0, "JSON serialization produced empty string"

        # Verify round-trip
        parsed = json.loads(json_str)
        assert parsed["INCOM_score"] == result["INCOM_score"]
        assert parsed["usage_frequency"] == result["usage_frequency"]

    finally:
        data_collection_interface.get_input = original_get_input


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
