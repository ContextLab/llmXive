"""
Unit tests for the schema generation script (T030a).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path to import the module if needed, 
# though we are testing the file content directly here.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_schema_file_generation():
    """Test that the schema generation script produces a valid JSON file."""
    # Import the main logic to test it directly or verify the file content
    from generate_schema import SCHEMA
    
    # Verify the schema structure
    assert "$schema" in SCHEMA
    assert "properties" in SCHEMA
    assert "participants" in SCHEMA["properties"]
    
    participant_item = SCHEMA["properties"]["participants"]["items"]
    assert "properties" in participant_item
    assert "participant_id" in participant_item["properties"]
    assert "condition" in participant_item["properties"]
    assert "clarification_questions" in participant_item["properties"]
    
    # Verify enum values
    assert participant_item["properties"]["condition"]["enum"] == ["llm", "human", "none"]

def test_schema_serialization():
    """Test that the schema can be serialized to JSON without error."""
    try:
        json_str = json.dumps(SCHEMA, indent=2)
        assert len(json_str) > 0
        # Verify it can be deserialized back
        loaded = json.loads(json_str)
        assert loaded == SCHEMA
    except Exception as e:
        pytest.fail(f"Schema serialization failed: {e}")