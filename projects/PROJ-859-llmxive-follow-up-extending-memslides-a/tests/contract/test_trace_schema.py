"""Contract tests for trace schema validation."""

import json
import pytest
from pathlib import Path
from code.contracts import validate_trace_artifact, validate_json_file

# Valid trace artifact for testing
VALID_TRACE = {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2023-10-01T12:00:00Z",
    "tool_sequence": [
        {
            "tool_name": "create_slide",
            "arguments": {"title": "Intro", "index": 0}
        },
        {
            "tool_name": "edit_text",
            "arguments": {"slide_id": 0, "text": "Hello World"}
        }
    ],
    "final_state": {
        "slides": [
            {"slide_id": 0, "title": "Intro", "content": ["Hello World"]}
        ]
    },
    "metadata": {
        "seed": 42,
        "sequence_length": 2,
        "exact_tool_sequence": ["create_slide", "edit_text"],
        "raw_arg_variance": 0.5
    }
}

INVALID_TRACE_MISSING_FIELD = {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "tool_sequence": [],
    "final_state": {"slides": []},
    "metadata": {}
}

INVALID_TRACE_BAD_ID = {
    "session_id": "not-a-uuid",
    "timestamp": "2023-10-01T12:00:00Z",
    "tool_sequence": [],
    "final_state": {"slides": []},
    "metadata": {"seed": 1, "sequence_length": 0, "exact_tool_sequence": [], "raw_arg_variance": 0.0}
}

def test_validate_valid_trace():
    """Test that a valid trace passes validation."""
    is_valid, error = validate_trace_artifact(VALID_TRACE)
    assert is_valid is True
    assert error is None

def test_validate_missing_field():
    """Test that a trace missing a required field fails."""
    is_valid, error = validate_trace_artifact(INVALID_TRACE_MISSING_FIELD)
    assert is_valid is False
    assert error is not None
    assert "timestamp" in error or "required" in error

def test_validate_bad_session_id():
    """Test that a trace with an invalid session ID fails."""
    is_valid, error = validate_trace_artifact(INVALID_TRACE_BAD_ID)
    assert is_valid is False
    assert error is not None
    assert "pattern" in error or "uuid" in error.lower()

def test_validate_json_file_valid(tmp_path):
    """Test validation of a valid JSON file."""
    file_path = tmp_path / "valid_trace.json"
    with open(file_path, 'w') as f:
        json.dump(VALID_TRACE, f)
    
    is_valid, error = validate_json_file(file_path, "trace.schema.yaml")
    assert is_valid is True
    assert error is None

def test_validate_json_file_invalid(tmp_path):
    """Test validation of an invalid JSON file."""
    file_path = tmp_path / "invalid_trace.json"
    with open(file_path, 'w') as f:
        json.dump(INVALID_TRACE_MISSING_FIELD, f)
    
    is_valid, error = validate_json_file(file_path, "trace.schema.yaml")
    assert is_valid is False
    assert error is not None

def test_validate_json_file_not_found():
    """Test validation of a non-existent file."""
    file_path = Path("/non/existent/path.json")
    is_valid, error = validate_json_file(file_path, "trace.schema.yaml")
    assert is_valid is False
    assert "not found" in error.lower() or "File not found" in error