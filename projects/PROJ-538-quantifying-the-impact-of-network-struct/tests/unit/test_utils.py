"""
Unit tests for code/utils.py.
Verifies error handling and logging infrastructure.
"""
import pytest
import logging
import json
from pathlib import Path
from code.utils import get_logger, DataAvailabilityError, VoronoiFailure, log_audit_event


class TestErrorHandling:
    """Tests for custom exceptions."""

    def test_data_availability_error(self):
        """Test DataAvailabilityError message handling."""
        msg = "Data not found"
        error = DataAvailabilityError(msg)
        assert str(error) == msg

    def test_voronoi_failure(self):
        """Test VoronoiFailure message handling."""
        msg = "Voronoi computation failed"
        error = VoronoiFailure(msg)
        assert str(error) == msg


class TestLogger:
    """Tests for the logging infrastructure."""

    def test_get_logger(self):
        """Test that get_logger returns a valid logger."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"

    def test_log_audit_event(self, test_config, test_data_dir):
        """Test that log_audit_event writes to the audit log."""
        audit_path = Path(test_config.audit_log_path)
        
        # Ensure the file exists (utils should create it, but we test the write)
        if not audit_path.exists():
            audit_path.write_text("[]")

        log_audit_event("TEST_EVENT", "test_details", test_config.audit_log_path)
        
        assert audit_path.exists()
        content = json.loads(audit_path.read_text())
        assert isinstance(content, list)
        assert len(content) >= 1
        assert content[-1]["event"] == "TEST_EVENT"
        assert content[-1]["details"] == "test_details"
