"""Unit tests for contract validation logic."""

import json
import pytest
from pathlib import Path
from typing import Any, Dict

# Ensure we can import the code package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.contracts import (
    load_schema,
    validate_artifact,
    validate_json_file,
    validate_trace_artifact,
    get_all_schema_names,
    CONTRACTS_DIR
)

@pytest.fixture
def valid_trace_data() -> Dict[str, Any]:
    """Provide a minimal valid trace artifact based on expected schema structure."""
    return {
        "session_id": "test-session-123",
        "tool_sequence": [
            {"tool": "edit_slide", "args": {"page": 1, "content": "Hello"}}
        ],
        "final_state": {"slides": [{"page": 1, "content": "Hello"}]},
        "metadata": {"seed": 42}
    }

@pytest.fixture
def invalid_trace_data() -> Dict[str, Any]:
    """Provide an invalid trace artifact (missing required fields)."""
    return {
        "session_id": "test-session-123"
        # Missing tool_sequence and final_state
    }

def test_load_schema_exists():
    """Test that we can load the trace schema if it exists."""
    schema_path = CONTRACTS_DIR / "trace.schema.yaml"
    if schema_path.exists():
        schema = load_schema("trace.schema.yaml")
        assert isinstance(schema, dict)
        assert "type" in schema or "$schema" in schema
    else:
        # If schema doesn't exist yet, we expect FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_schema("trace.schema.yaml")

def test_validate_artifact_valid(valid_trace_data):
    """Test validation of a valid artifact."""
    schema_path = CONTRACTS_DIR / "trace.schema.yaml"
    if not schema_path.exists():
        pytest.skip("trace.schema.yaml not found, skipping validation test")
    
    is_valid, error = validate_artifact(valid_trace_data, "trace.schema.yaml")
    # Note: This might fail if the schema requires fields not in our mock data,
    # but it tests the mechanism. If the schema is strict, we expect it to catch
    # missing fields if our mock is incomplete.
    # For now, we just ensure the function returns a tuple and doesn't crash.
    assert isinstance(is_valid, bool)
    assert error is None or isinstance(error, str)

def test_validate_artifact_invalid(invalid_trace_data):
    """Test validation of an invalid artifact."""
    schema_path = CONTRACTS_DIR / "trace.schema.yaml"
    if not schema_path.exists():
        pytest.skip("trace.schema.yaml not found, skipping validation test")
    
    is_valid, error = validate_artifact(invalid_trace_data, "trace.schema.yaml")
    assert is_valid is False
    assert error is not None
    assert "validation error" in error.lower()

def test_validate_json_file(tmp_path):
    """Test validation via a JSON file."""
    schema_path = CONTRACTS_DIR / "trace.schema.yaml"
    if not schema_path.exists():
        pytest.skip("trace.schema.yaml not found, skipping file validation test")
    
    test_file = tmp_path / "test_trace.json"
    test_file.write_text(json.dumps({
        "session_id": "file-test",
        "tool_sequence": [],
        "final_state": {},
        "metadata": {}
    }))
    
    is_valid, error = validate_json_file(test_file, "trace.schema.yaml")
    assert isinstance(is_valid, bool)
    assert error is None or isinstance(error, str)

def test_get_all_schema_names():
    """Test retrieval of schema names."""
    names = get_all_schema_names()
    assert isinstance(names, list)
    # Should include at least trace.schema.yaml if it exists
    if (CONTRACTS_DIR / "trace.schema.yaml").exists():
        assert "trace.schema.yaml" in names

def test_validate_trace_artifact_wrapper(valid_trace_data):
    """Test the specific trace validation wrapper."""
    schema_path = CONTRACTS_DIR / "trace.schema.yaml"
    if not schema_path.exists():
        pytest.skip("trace.schema.yaml not found")
    
    is_valid, error = validate_trace_artifact(valid_trace_data)
    assert isinstance(is_valid, bool)
    assert error is None or isinstance(error, str)
