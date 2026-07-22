"""
Unit tests for code/simulator/validator.py (T019c).

These tests verify that the runtime schema validation logic correctly:
1. Accepts valid session data conforming to contracts/session.schema.yaml.
2. Rejects data with missing required fields.
3. Rejects data with incorrect types.
4. Rejects data with invalid enum values.
5. Rejects data violating min/max constraints.
"""
import pytest
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import tempfile

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulator.validator import validate_session, _load_schema

# Sample valid data based on contracts/session.schema.yaml
VALID_SESSION_DATA = {
    "participant_id": "P001",
    "disability_type": "visual",
    "interface_type": "traditional",
    "sequence": "traditional_explainable",
    "start_time": "2023-10-27T10:00:00",
    "end_time": "2023-10-27T10:15:00",
    "error_count": 2,
    "explanation_engagement_time_seconds": 45.5,
    "sus_score": 85,
    "status": "complete"
}

def test_validate_session_valid_data():
    """Test that valid data passes validation."""
    assert validate_session(VALID_SESSION_DATA) is True

def test_validate_session_missing_required_field():
    """Test that missing required fields raise ValueError."""
    invalid_data = VALID_SESSION_DATA.copy()
    del invalid_data["participant_id"]
    
    with pytest.raises(ValueError) as exc_info:
        validate_session(invalid_data)
    
    assert "Missing required field: 'participant_id'" in str(exc_info.value)

def test_validate_session_invalid_enum():
    """Test that invalid enum values raise ValueError."""
    invalid_data = VALID_SESSION_DATA.copy()
    invalid_data["interface_type"] = "invalid_interface"
    
    with pytest.raises(ValueError) as exc_info:
        validate_session(invalid_data)
    
    assert "must be one of" in str(exc_info.value)

def test_validate_session_invalid_type():
    """Test that incorrect types raise ValueError."""
    invalid_data = VALID_SESSION_DATA.copy()
    invalid_data["error_count"] = "not_an_integer"
    
    with pytest.raises(ValueError) as exc_info:
        validate_session(invalid_data)
    
    assert "must be an integer" in str(exc_info.value)

def test_validate_session_out_of_range():
    """Test that values outside min/max constraints raise ValueError."""
    invalid_data = VALID_SESSION_DATA.copy()
    invalid_data["sus_score"] = 150  # Max is 100
    
    with pytest.raises(ValueError) as exc_info:
        validate_session(invalid_data)
    
    assert "must be <=" in str(exc_info.value)

def test_validate_session_invalid_datetime():
    """Test that invalid date-time format raises ValueError."""
    invalid_data = VALID_SESSION_DATA.copy()
    invalid_data["start_time"] = "not-a-date"
    
    with pytest.raises(ValueError) as exc_info:
        validate_session(invalid_data)
    
    assert "must be a valid ISO date-time" in str(exc_info.value)

def test_validate_session_optional_field_missing():
    """Test that missing optional fields do not raise errors."""
    # dropout_reason is optional
    data_without_optional = {k: v for k, v in VALID_SESSION_DATA.items() if k != "dropout_reason"}
    assert validate_session(data_without_optional) is True

def test_load_schema_exists():
    """Test that the schema file can be loaded."""
    schema = _load_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "required" in schema