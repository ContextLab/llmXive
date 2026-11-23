import json
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the module functions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data_collection import (
    export_raw_data,
    calculate_checksum,
    load_existing_logs,
    save_logs,
    ensure_data_directory,
    PARTICIPANT_LOGS_FILE,
    CHECKSUM_FILE
)

class TestDataCollectionExport:
    """Unit tests for T020: Raw data export function with checksum generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_raw_dir = os.path.join(self.test_dir, "raw")
        self.original_data_dir = self.test_dir
        
        # Mock the constants
        self.original_raw_dir_path = PARTICIPANT_LOGS_FILE
        self.original_checksum_path = CHECKSUM_FILE
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_export_raw_data_creates_file(self):
        """Test that export_raw_data creates the output file."""
        test_logs = [
            {
                "participant_id": "PART-1001",
                "condition": "LLM",
                "session_start": "2024-01-01T10:00:00",
                "session_end": "2024-01-01T10:30:00",
                "final_time": 1800,
                "status": "completed"
            }
        ]
        
        output_path = os.path.join(self.test_dir, "test_logs.json")
        result = export_raw_data(test_logs, output_path)
        
        assert os.path.exists(output_path)
        assert result["path"] == output_path
        assert result["count"] == 1

    def test_export_raw_data_generates_checksum(self):
        """Test that export_raw_data generates and records a checksum."""
        test_logs = [
            {
                "participant_id": "PART-1002",
                "condition": "Human",
                "session_start": "2024-01-01T11:00:00",
                "final_time": 1200
            }
        ]
        
        output_path = os.path.join(self.test_dir, "test_logs_2.json")
        checksum_file = os.path.join(self.test_dir, "checksums.txt")
        
        # Temporarily override CHECKSUM_FILE for testing
        with patch('data_collection.CHECKSUM_FILE', checksum_file):
            result = export_raw_data(test_logs, output_path)
        
        assert "checksum" in result
        assert len(result["checksum"]) == 64  # SHA256 hex length
        
        # Verify checksum file was created
        assert os.path.exists(checksum_file)

    def test_export_raw_data_valid_json(self):
        """Test that the exported file is valid JSON."""
        test_logs = [
            {"id": 1, "name": "test"},
            {"id": 2, "name": "test2"}
        ]
        
        output_path = os.path.join(self.test_dir, "valid_json_test.json")
        export_raw_data(test_logs, output_path)
        
        with open(output_path, 'r') as f:
            loaded_logs = json.load(f)
        
        assert loaded_logs == test_logs

    def test_export_raw_data_empty_list(self):
        """Test exporting an empty list of logs."""
        output_path = os.path.join(self.test_dir, "empty_logs.json")
        result = export_raw_data([], output_path)
        
        assert result["count"] == 0
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            content = json.load(f)
        assert content == []

    def test_export_raw_data_with_help_requests(self):
        """Test exporting logs with help request data."""
        test_logs = [
            {
                "participant_id": "PART-1003",
                "condition": "None",
                "session_start": "2024-01-01T12:00:00",
                "session_end": "2024-01-01T12:45:00",
                "help_requests": [
                    {"timestamp": "2024-01-01T12:10:00", "content": "How do I start?"},
                    {"timestamp": "2024-01-01T12:20:00", "content": "Why is this failing?"}
                ],
                "helpfulness_rating": 4,
                "intervention_flag": False,
                "status": "completed",
                "abandoned": False
            }
        ]
        
        output_path = os.path.join(self.test_dir, "help_requests_test.json")
        result = export_raw_data(test_logs, output_path)
        
        assert result["count"] == 1
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded[0]["help_requests"]) == 2
        assert loaded[0]["helpfulness_rating"] == 4

    def test_checksum_consistency(self):
        """Test that the same data produces the same checksum."""
        test_logs = [{"id": 1}]
        output_path = os.path.join(self.test_dir, "checksum_test.json")
        
        result1 = export_raw_data(test_logs, output_path)
        checksum1 = result1["checksum"]
        
        result2 = export_raw_data(test_logs, output_path)
        checksum2 = result2["checksum"]
        
        assert checksum1 == checksum2

    def test_export_raw_data_default_path(self):
        """Test that export_raw_data uses the default path when not specified."""
        # This test is more of a integration test since it depends on the module's constant
        # We'll verify the function accepts the default parameter
        test_logs = [{"id": 1}]
        
        # Just ensure it doesn't raise an exception with default path
        # In a real environment, this would write to data/raw/participant_logs.json
        try:
            # We won't actually run this in the temp dir to avoid side effects
            # Instead, we verify the function signature accepts the default
            import inspect
            sig = inspect.signature(export_raw_data)
            params = list(sig.parameters.keys())
            assert 'output_path' in params
        except Exception as e:
            pytest.fail(f"Function signature check failed: {e}")

    def test_export_raw_data_creates_directory(self):
        """Test that export_raw_data creates the output directory if it doesn't exist."""
        test_logs = [{"id": 1}]
        nested_path = os.path.join(self.test_dir, "nested", "deep", "logs.json")
        
        result = export_raw_data(test_logs, nested_path)
        
        assert os.path.exists(nested_path)
        assert result["count"] == 1

    def test_export_raw_data_timestamp(self):
        """Test that the export result includes a timestamp."""
        test_logs = [{"id": 1}]
        output_path = os.path.join(self.test_dir, "timestamp_test.json")
        
        result = export_raw_data(test_logs, output_path)
        
        assert "timestamp" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["timestamp"])