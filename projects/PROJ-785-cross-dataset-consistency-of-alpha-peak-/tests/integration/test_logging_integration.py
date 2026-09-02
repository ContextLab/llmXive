import pytest
import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logger import configure_root_logger, log_structured_event, get_logger
from config import get_project_root

class TestLoggingIntegration:
    def test_log_file_creation(self, tmp_path):
        """
        Integration test to verify that the logging system creates a log file
        in the state directory and writes structured JSON entries.
        """
        # Setup a temporary state directory for testing
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        log_file = state_dir / "test_pipeline.log"
        
        # Configure logger with the temp file
        configure_root_logger(log_file=str(log_file))
        
        # Log an event
        log_structured_event(
            event_type="INTEGRATION_TEST",
            message="Verifying log file creation",
            level="INFO",
            test_id="T005-001"
        )
        
        # Verify file exists
        assert log_file.exists(), "Log file was not created"
        
        # Verify file content is valid JSON
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0, "Log file is empty"
            
            # Parse the last line as JSON
            last_entry = json.loads(lines[-1])
            assert last_entry["message"] == "Verifying log file creation"
            assert last_entry["context"]["test_id"] == "T005-001"
            assert last_entry["level"] == "INFO"

    def test_multiple_log_entries(self, tmp_path):
        """
        Verify that multiple log entries are appended correctly.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        log_file = state_dir / "multi_test.log"
        
        configure_root_logger(log_file=str(log_file))
        
        # Log multiple events
        for i in range(3):
            log_structured_event(
                event_type="MULTI_TEST",
                message=f"Entry {i}",
                level="INFO",
                index=i
            )
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
            
            for i, line in enumerate(lines):
                entry = json.loads(line)
                assert entry["context"]["index"] == i
                assert entry["message"] == f"Entry {i}"

    def test_exception_logging(self, tmp_path):
        """
        Verify that exceptions are logged with full traceback.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        log_file = state_dir / "exception_test.log"
        
        configure_root_logger(log_file=str(log_file))
        
        logger = get_logger()
        try:
            raise ValueError("Integration test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            logger.error("An error occurred", exc_info=exc_info)
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            # Verify exception type is in the log
            assert "ValueError" in content
            assert "Integration test exception" in content
            assert "traceback" in content.lower()
