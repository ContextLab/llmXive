"""
Unit tests for the RawDataLogger module (T019).

These tests verify:
1. Successful logging of complete sessions.
2. Successful logging of incomplete sessions (dropouts).
3. Strict rejection of invalid data (schema validation).
4. Failure when schema file is missing.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simulator.raw_data_logger import RawDataLogger
from simulator.data_validator import DataValidator

class TestRawDataLogger:

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Mock settings to use a temporary directory for raw data."""
        with patch('simulator.raw_data_logger.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.project_root = tmp_path
            mock_get_settings.return_value = mock_settings
            yield tmp_path

    @pytest.fixture
    def valid_session_data(self):
        """Fixture for valid session data."""
        return {
            "participant_id": "P-001",
            "disability_type": "visual_impairment",
            "interface_type": "Explainable",
            "sequence": "Explainable->Traditional",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "error_count": 0,
            "explanation_engagement_time_seconds": 10.5,
            "sus_score": 90.0,
            "status": "complete",
            "dropout_reason": None
        }

    @pytest.fixture
    def schema_content(self):
        """Return the expected schema content string."""
        return """
        type: object
        required:
          - participant_id
          - status
        properties:
          participant_id:
            type: string
          status:
            type: string
        additionalProperties: false
        """

    def test_log_complete_session(self, mock_settings, valid_session_data):
        """Test that a valid complete session is logged to disk."""
        # Ensure schema file exists in the mock project root
        schema_path = mock_settings / "contracts" / "session.schema.yaml"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text("type: object\nproperties:\n  participant_id:\n    type: string\n  status:\n    type: string\nadditionalProperties: false\n")

        logger = RawDataLogger()
        file_path = logger.log_session(valid_session_data)

        # Verify file exists
        assert os.path.exists(file_path)
        
        # Verify content
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["participant_id"] == "P-001"
        assert loaded_data["status"] == "complete"
        assert "file_checksum" in loaded_data
        assert "logged_at" in loaded_data

    def test_log_incomplete_session(self, mock_settings):
        """Test logging a session with status 'incomplete'."""
        # Setup schema
        schema_path = mock_settings / "contracts" / "session.schema.yaml"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text("type: object\nproperties:\n  participant_id:\n    type: string\n  status:\n    type: string\nadditionalProperties: false\n")

        incomplete_data = {
            "participant_id": "P-002",
            "disability_type": "motor_impairment",
            "interface_type": "Traditional",
            "sequence": "Traditional->Explainable",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "error_count": 5,
            "explanation_engagement_time_seconds": 0,
            "sus_score": None,
            "status": "incomplete",
            "dropout_reason": "frustration"
        }

        logger = RawDataLogger()
        file_path = logger.log_session(incomplete_data)

        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["status"] == "incomplete"
        assert loaded_data["dropout_reason"] == "frustration"

    def test_invalid_data_rejected(self, mock_settings, valid_session_data):
        """Test that invalid data (e.g., missing required field) raises ValueError."""
        # Setup schema
        schema_path = mock_settings / "contracts" / "session.schema.yaml"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text("type: object\nrequired:\n  - participant_id\nproperties:\n  participant_id:\n    type: string\nadditionalProperties: false\n")

        # Remove required field
        invalid_data = valid_session_data.copy()
        del invalid_data["participant_id"]

        logger = RawDataLogger()
        
        with pytest.raises(ValueError, match="Session validation failed"):
            logger.log_session(invalid_data)

    def test_missing_schema_raises_error(self, mock_settings, valid_session_data):
        """Test that missing schema file raises FileNotFoundError."""
        # Do NOT create the schema file
        
        logger = RawDataLogger()
        
        with pytest.raises(FileNotFoundError, match="Schema file missing"):
            logger.log_session(valid_session_data)

    def test_log_dropout_helper(self, mock_settings):
        """Test the log_dropout helper method."""
        # Setup schema
        schema_path = mock_settings / "contracts" / "session.schema.yaml"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text("type: object\nproperties:\n  participant_id:\n    type: string\n  status:\n    type: string\nadditionalProperties: false\n")

        logger = RawDataLogger()
        
        start = datetime.now()
        end = datetime.now()
        
        path = logger.log_dropout(
            participant_id="P-003",
            interface_type="Explainable",
            sequence="Explainable->Traditional",
            dropout_reason="time_constraint",
            start_time=start,
            end_time=end,
            metrics_partial={"error_count": 1, "disability_type": "cognitive_impairment"}
        )

        assert os.path.exists(path)
        with open(path, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "incomplete"
        assert data["dropout_reason"] == "time_constraint"
        assert data["participant_id"] == "P-003"