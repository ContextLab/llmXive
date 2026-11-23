"""
Unit tests for the session logger module.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.simulator.session_logger import log_session, SessionLogger
from code.simulator.validator import load_schema

@pytest.fixture
def valid_session_data():
    now = datetime.utcnow().isoformat()
    return {
        "participant_id": "P001",
        "disability_type": "visual",
        "interface_type": "explainable",
        "sequence": "Traditional->Explainable",
        "start_time": now,
        "end_time": now,
        "error_count": 2,
        "explanation_engagement_time_seconds": 10.5,
        "sus_score": 75,
        "status": "complete",
        "dropout_reason": None
    }

@pytest.fixture
def invalid_session_data():
    # Missing required field
    return {
        "participant_id": "P002",
        "interface_type": "traditional",
        # Missing disability_type, sequence, etc.
    }

def test_log_session_success(valid_session_data, tmp_path):
    """Test that a valid session is logged correctly."""
    # Mock the data directory
    from code.simulator import session_logger
    original_dir = session_logger._RAW_DATA_DIR
    session_logger._RAW_DATA_DIR = tmp_path
    
    try:
        path = log_session(valid_session_data, session_id="test_001")
        
        assert os.path.exists(path)
        assert "session_test_001.json" in path
        
        with open(path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["participant_id"] == "P001"
        assert loaded_data["status"] == "complete"
        assert "logged_at" in loaded_data
    finally:
        session_logger._RAW_DATA_DIR = original_dir

def test_log_session_validation_failure(invalid_session_data, tmp_path):
    """Test that invalid data raises ValueError."""
    from code.simulator import session_logger
    original_dir = session_logger._RAW_DATA_DIR
    session_logger._RAW_DATA_DIR = tmp_path
    
    try:
        with pytest.raises(ValueError) as exc_info:
            log_session(invalid_session_data, session_id="test_002")
        
        assert "validation failed" in str(exc_info.value).lower()
    finally:
        session_logger._RAW_DATA_DIR = original_dir

def test_log_session_missing_schema(tmp_path):
    """Test that missing schema raises FileNotFoundError."""
    # Create a temporary schema path that doesn't exist
    fake_schema = tmp_path / "nonexistent.schema.yaml"
    
    # We can't easily test the global function without mocking the schema path,
    # but we can test the class initialization
    with pytest.raises(FileNotFoundError):
        SessionLogger(schema_path=fake_schema)

def test_schema_contains_required_fields():
    """Verify the schema file exists and contains required fields."""
    schema_path = project_root / "contracts" / "session.schema.yaml"
    assert schema_path.exists(), "contracts/session.schema.yaml must exist"
    
    schema = load_schema(schema_path)
    required_fields = [
        "participant_id", "disability_type", "interface_type", "sequence",
        "start_time", "end_time", "error_count", "explanation_engagement_time_seconds",
        "sus_score", "status", "dropout_reason"
    ]
    
    schema_props = schema.get("properties", {})
    for field in required_fields:
        assert field in schema_props, f"Schema missing required field: {field}"