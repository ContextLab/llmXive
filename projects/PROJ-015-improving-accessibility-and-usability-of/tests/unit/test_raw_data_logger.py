import pytest
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from simulator.raw_data_logger import RawDataLogger, load_schema, validate_session_against_schema
from utils.logger import get_logger

logger = get_logger(__name__)

class TestRawDataLogger:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.temp_dir = tmp_path
        self.logger = RawDataLogger(output_dir=self.temp_dir)

    def test_log_valid_session(self):
        """Test logging a valid session creates a file."""
        session_data = {
            "participant_id": "P001",
            "disability_type": "visual",
            "interface_type": "explainable",
            "sequence": "traditional_explainable",
            "error_count": 2,
            "explanation_engagement_time_seconds": 15.5,
            "sus_score": 85,
            "status": "complete",
            "start_time": "2023-01-01T10:00:00",
            "end_time": "2023-01-01T10:30:00"
        }
        
        file_path = self.logger.log_session(session_data)
        
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["participant_id"] == "P001"
        assert loaded["status"] == "complete"

    def test_log_missing_required_field(self):
        """Test that missing required fields raise an error."""
        session_data = {
            "interface_type": "traditional",
            "sequence": "traditional_explainable",
            "start_time": "2023-01-01T10:00:00",
            "end_time": "2023-01-01T10:30:00"
            # Missing participant_id, disability_type, etc.
        }
        
        with pytest.raises(ValueError) as excinfo:
            self.logger.log_session(session_data)
        
        assert "Missing required field" in str(excinfo.value)

    def test_log_invalid_enum_value(self):
        """Test that invalid enum values raise an error."""
        session_data = {
            "participant_id": "P001",
            "disability_type": "visual",
            "interface_type": "invalid_interface", # Not in enum
            "sequence": "traditional_explainable",
            "error_count": 0,
            "explanation_engagement_time_seconds": 0.0,
            "sus_score": 50,
            "status": "complete",
            "start_time": "2023-01-01T10:00:00",
            "end_time": "2023-01-01T10:30:00"
        }
        
        with pytest.raises(ValueError) as excinfo:
            self.logger.log_session(session_data)
        
        assert "not in allowed enum" in str(excinfo.value)

    def test_log_negative_error_count(self):
        """Test that negative error count raises an error."""
        session_data = {
            "participant_id": "P001",
            "disability_type": "visual",
            "interface_type": "traditional",
            "sequence": "traditional_explainable",
            "error_count": -1, # Invalid
            "explanation_engagement_time_seconds": 0.0,
            "sus_score": 50,
            "status": "complete",
            "start_time": "2023-01-01T10:00:00",
            "end_time": "2023-01-01T10:30:00"
        }
        
        with pytest.raises(ValueError) as excinfo:
            self.logger.log_session(session_data)
        
        assert "less than minimum" in str(excinfo.value)

    def test_schema_loading_failure(self):
        """Test that missing schema file raises FileNotFoundError."""
        # Temporarily move schema to simulate missing file
        schema_path = Path("contracts/session.schema.yaml")
        backup_path = Path("contracts/session.schema.yaml.bak")
        
        if schema_path.exists():
            schema_path.rename(backup_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                load_schema()
        finally:
            # Restore schema
            if backup_path.exists():
                backup_path.rename(schema_path)
