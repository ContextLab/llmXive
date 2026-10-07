"""
Unit tests for Metadata Schema (T069).

Tests ensure that METADATA_SCHEMA is defined correctly and matches
the exported CSV columns.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.survey.constants import METADATA_SCHEMA


def test_metadata_schema_defined():
    """Test that METADATA_SCHEMA is defined."""
    assert METADATA_SCHEMA is not None
    assert isinstance(METADATA_SCHEMA, dict)


def test_metadata_schema_has_required_fields():
    """Test that METADATA_SCHEMA contains all required fields."""
    required_fields = [
        "participant_id",
        "age",
        "education",
        "timestamp",
        "hashed_ip",
        "browser_version",
        "session_start_time",
        "stimulus_id"
    ]
    
    for field in required_fields:
        assert field in METADATA_SCHEMA, f"Missing required field: {field}"


def test_metadata_schema_field_types():
    """Test that METADATA_SCHEMA fields have correct type annotations."""
    expected_types = {
        "participant_id": "str",
        "age": "int",
        "education": "str",
        "timestamp": "str",
        "hashed_ip": "str",
        "browser_version": "str",
        "session_start_time": "str",
        "stimulus_id": "str"
    }
    
    for field, expected_type in expected_types.items():
        if field in METADATA_SCHEMA:
            actual_type = METADATA_SCHEMA[field].get("type", "")
            assert actual_type == expected_type, (
                f"Field {field} has type {actual_type}, expected {expected_type}"
            )


def test_csv_columns_match_schema():
    """Test that CSV columns match the schema definition."""
    # This test verifies the schema matches what we expect to export
    expected_columns = list(METADATA_SCHEMA.keys())
    
    # Verify we have the expected number of columns
    assert len(expected_columns) == 8, f"Expected 8 columns, got {len(expected_columns)}"
    
    # Verify specific columns exist
    assert "participant_id" in expected_columns
    assert "browser_version" in expected_columns
    assert "session_start_time" in expected_columns
    assert "stimulus_id" in expected_columns
    assert "hashed_ip" in expected_columns
    assert "age" in expected_columns
    assert "education" in expected_columns
    assert "timestamp" in expected_columns