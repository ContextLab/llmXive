import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
import logging
import sys

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logging_config import setup_logging

class TestLogging:
    """
    Unit tests for the logging configuration, specifically the JSONL handler.
    """

    def setup_method(self):
        """Setup temporary directories for test logs."""
        self.temp_dir = tempfile.mkdtemp()
        self.jsonl_log_path = os.path.join(self.temp_dir, "skipped_records.log")
        self.general_log_path = os.path.join(self.temp_dir, "general.log")

    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Reset root logger handlers to avoid side effects in other tests
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def test_jsonl_handler_creation(self):
        """Test that setup_logging creates a JSONL handler when jsonl_log_file is provided."""
        logger = setup_logging(jsonl_log_file=self.jsonl_log_path)
        
        # Check that the logger has handlers
        assert len(logger.handlers) >= 1
        
        # Find the JsonLHandler
        jsonl_handler_found = False
        for handler in logger.handlers:
            if hasattr(handler, 'filepath') and str(handler.filepath) == self.jsonl_log_path:
                jsonl_handler_found = True
                break
        
        assert jsonl_handler_found, "JsonLHandler not found in logger handlers"

    def test_jsonl_handler_writes_valid_json(self):
        """Test that the JSONL handler writes valid JSON lines."""
        logger = setup_logging(
            log_level=logging.WARNING,
            jsonl_log_file=self.jsonl_log_path
        )
        
        # Log a message with extra data
        extra_data = {
            "error_code": "TEST_ERROR",
            "reason": "test_reason",
            "dataset_source": "test_source"
        }
        logger.warning("Test message", extra={"extra_data": extra_data})
        
        # Check file content
        assert os.path.exists(self.jsonl_log_path), "Log file was not created"
        
        with open(self.jsonl_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 1, "Expected exactly one log line"
        
        # Parse JSON
        try:
            log_entry = json.loads(lines[0])
        except json.JSONDecodeError:
            pytest.fail("Log entry is not valid JSON")
        
        # Verify structure
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert log_entry["level"] == "WARNING"
        assert "message" in log_entry
        assert log_entry["message"] == "Test message"
        assert "logger" in log_entry
        
        # Verify extra data
        assert log_entry["error_code"] == "TEST_ERROR"
        assert log_entry["reason"] == "test_reason"
        assert log_entry["dataset_source"] == "test_source"

    def test_skipped_record_logging(self):
        """Test the specific use case of logging a skipped record."""
        from src.data_loader import log_skipped_record
        
        logger = setup_logging(
            log_level=logging.WARNING,
            jsonl_log_file=self.jsonl_log_path
        )
        
        log_skipped_record(
            logger,
            reason="Missing pre_test_score",
            record_id="record_123",
            dataset_source="test_data.csv"
        )
        
        with open(self.jsonl_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) >= 1
        log_entry = json.loads(lines[-1])
        
        assert log_entry["error_code"] == "SKIPPED_RECORD"
        assert log_entry["reason"] == "Missing pre_test_score"
        assert log_entry["record_id"] == "record_123"
        assert log_entry["dataset_source"] == "test_data.csv"

    def test_no_jsonl_handler_when_not_specified(self):
        """Test that no JSONL handler is created when jsonl_log_file is None."""
        logger = setup_logging()
        
        jsonl_handler_found = False
        for handler in logger.handlers:
            if hasattr(handler, 'filepath'):
                jsonl_handler_found = True
                break
        
        assert not jsonl_handler_found, "JsonLHandler should not be created when jsonl_log_file is None"

    def test_directory_creation(self):
        """Test that setup_logging creates parent directories for log files."""
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "skipped.log")
        
        logger = setup_logging(jsonl_log_file=nested_path)
        
        assert os.path.exists(nested_path), "Log file was not created in nested directory"
        assert os.path.isdir(os.path.dirname(nested_path)), "Parent directory was not created"