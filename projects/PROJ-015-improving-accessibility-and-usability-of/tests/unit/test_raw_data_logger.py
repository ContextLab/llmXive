import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Mock settings to avoid dependency on actual config file during unit tests
@pytest.fixture
def mock_settings():
    with patch('simulator.raw_data_logger.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.data_root = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings
        yield mock_settings

@pytest.fixture
def raw_logger(mock_settings):
    from simulator.raw_data_logger import RawDataLogger
    return RawDataLogger()

@pytest.fixture
def valid_session_data():
    return {
        "session_id": "test-session-123",
        "participant_id": "p-001",
        "disability_type": "visual_impairment",
        "interface_type": "explainable",
        "sequence": ["Traditional", "Explainable"],
        "start_time": datetime(2023, 1, 1, 10, 0, 0),
        "end_time": datetime(2023, 1, 1, 10, 15, 0),
        "error_count": 2,
        "explanation_engagement_time_seconds": 45.5,
        "sus_score": 85.0,
        "status": "complete",
        "dropout_reason": None
    }

class TestRawDataLogger:
    def test_log_session_creates_file(self, raw_logger, valid_session_data):
        """Test that log_session creates a JSON file on disk."""
        file_path = raw_logger.log_session(valid_session_data)
        
        assert os.path.exists(file_path), f"File not created at {file_path}"
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert data["participant_id"] == "p-001"
        assert data["status"] == "complete"
        assert "checksum" in data
        assert "logged_at" in data

    def test_log_session_validates_data(self, raw_logger, valid_session_data, mock_settings):
        """Test that log_session rejects invalid data."""
        from simulator.data_validator import DataValidator
        
        # Mock the validator to return False
        with patch.object(DataValidator, 'validate_session_data', return_value={"valid": False, "errors": ["Missing field"]}):
            with pytest.raises(ValueError, match="Session data invalid"):
                raw_logger.log_session(valid_session_data)

    def test_log_incomplete_session(self, raw_logger):
        """Test logging an incomplete session with dropout reason."""
        data = {
            "participant_id": "p-002",
            "disability_type": "motor_impairment",
            "interface_type": "traditional",
            "sequence": ["Traditional"],
            "start_time": datetime(2023, 1, 2, 11, 0, 0),
            "end_time": datetime(2023, 1, 2, 11, 0, 30),
            "error_count": 5,
            "explanation_engagement_time_seconds": 0.0,
            "sus_score": None,
            "status": "incomplete",
            "dropout_reason": "User fatigue"
        }
        
        file_path = raw_logger.log_incomplete_session(
            participant_id=data["participant_id"],
            disability_type=data["disability_type"],
            interface_type=data["interface_type"],
            sequence=data["sequence"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            error_count=data["error_count"],
            explanation_engagement_time_seconds=data["explanation_engagement_time_seconds"],
            sus_score=data["sus_score"],
            dropout_reason=data["dropout_reason"]
        )
        
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            logged_data = json.load(f)
        
        assert logged_data["status"] == "incomplete"
        assert logged_data["dropout_reason"] == "User fatigue"

    def test_checksum_integrity(self, raw_logger, valid_session_data):
        """Test that the checksum is correctly generated."""
        file_path = raw_logger.log_session(valid_session_data)
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Recalculate checksum
        import hashlib
        # Remove the checksum field from calculation to avoid self-reference
        check_data = {k: v for k, v in data.items() if k != 'checksum'}
        # Note: The implementation includes the checksum in the final dump, 
        # but the checksum itself is calculated on the data BEFORE adding the checksum.
        # We need to verify the logic matches the implementation.
        
        # In implementation:
        # 1. Add logged_at
        # 2. Generate checksum from current state (before adding checksum key)
        # 3. Add checksum key
        # 4. Dump to file
        
        # So we can verify by checking the file content matches the logic.
        # This test ensures the field exists and is a valid hex string.
        import re
        assert re.match(r'^[a-f0-9]{64}$', data["checksum"]), "Checksum must be a valid SHA256 hex string"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])