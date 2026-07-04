"""
Tests for data schema definitions (T007a).

Verifies that the DataVersion schema structure matches requirements.
"""
import json
import time
from code.data.schema import DataVersion


def test_schema_structure():
    """Verify the DataVersion schema has the required fields."""
    # Create a valid instance based on the TypedDict definition
    valid_record: DataVersion = {
        "source_url": "https://example.com/data.csv",
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Verify JSON serialization works (basic sanity check)
    json_str = json.dumps(valid_record)
    parsed = json.loads(json_str)

    assert "source_url" in parsed
    assert "checksum_sha256" in parsed
    assert "timestamp" in parsed
    assert isinstance(parsed["source_url"], str)
    assert isinstance(parsed["checksum_sha256"], str)
    assert isinstance(parsed["timestamp"], str)

def test_schema_field_constraints():
    """Verify field constraints implied by the schema."""
    # Check that the fields match the task description exactly
    required_fields = {"source_url", "checksum_sha256", "timestamp"}
    
    # The TypedDict keys represent the schema structure
    # We verify the variable annotation exists and is correct
    import inspect
    annotations = DataVersion.__annotations__
    
    assert set(annotations.keys()) == required_fields