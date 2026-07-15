"""
Contract test for error logging infrastructure.
Verifies that code/utils.py logs the specific keys 'unmatched_participant_ids'
and 'image_processing_failures' when triggered, with correct structured JSON format.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger, log_structured_error


class TestErrorLoggingContract:
    """
    Contract tests ensuring the error logging system adheres to spec requirements.
    """

    def test_unmatched_participant_ids_logging(self, caplog):
        """
        Verify that 'unmatched_participant_ids' error type is logged with
        the correct structured JSON format and key presence.
        """
        logger = get_logger("test_unmatched")
        
        # Clear existing handlers to avoid noise in test output
        logger.handlers.clear()
        
        # Create a handler that captures log records
        handler = logging.Handler()
        handler.setLevel(logging.ERROR)
        log_records = []
        
        def emit(record):
            log_records.append(record)
        
        handler.emit = emit
        logger.addHandler(handler)
        
        # Trigger the specific error
        details = {
            "missing_ids": ["P001", "P002"],
            "found_ids": ["P003", "P004"],
            "total_mismatch": 2
        }
        
        log_structured_error(logger, "unmatched_participant_ids", details)
        
        # Assert we captured a log record
        assert len(log_records) == 1
        record = log_records[0]
        
        # Verify it was logged at ERROR level
        assert record.levelno == logging.ERROR
        
        # Parse the JSON message
        try:
            parsed_message = json.loads(record.getMessage())
        except json.JSONDecodeError:
            pytest.fail("Log message is not valid JSON")
        
        # Verify required keys exist
        assert "error_type" in parsed_message
        assert "timestamp" in parsed_message
        assert "details" in parsed_message
        
        # Verify specific error type
        assert parsed_message["error_type"] == "unmatched_participant_ids"
        
        # Verify details contain the expected keys
        assert "missing_ids" in parsed_message["details"]
        assert "found_ids" in parsed_message["details"]
        assert "total_mismatch" in parsed_message["details"]

    def test_image_processing_failures_logging(self, caplog):
        """
        Verify that 'image_processing_failures' error type is logged with
        the correct structured JSON format and key presence.
        """
        logger = get_logger("test_image_fail")
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create a handler that captures log records
        handler = logging.Handler()
        handler.setLevel(logging.ERROR)
        log_records = []
        
        def emit(record):
            log_records.append(record)
        
        handler.emit = emit
        logger.addHandler(handler)
        
        # Trigger the specific error
        details = {
            "image_path": "data/raw/workspace_001.jpg",
            "error_message": "Could not detect edges",
            "processing_stage": "edge_detection"
        }
        
        log_structured_error(logger, "image_processing_failures", details)
        
        # Assert we captured a log record
        assert len(log_records) == 1
        record = log_records[0]
        
        # Verify it was logged at ERROR level
        assert record.levelno == logging.ERROR
        
        # Parse the JSON message
        try:
            parsed_message = json.loads(record.getMessage())
        except json.JSONDecodeError:
            pytest.fail("Log message is not valid JSON")
        
        # Verify required keys exist
        assert "error_type" in parsed_message
        assert "timestamp" in parsed_message
        assert "details" in parsed_message
        
        # Verify specific error type
        assert parsed_message["error_type"] == "image_processing_failures"
        
        # Verify details contain the expected keys
        assert "image_path" in parsed_message["details"]
        assert "error_message" in parsed_message["details"]
        assert "processing_stage" in parsed_message["details"]

    def test_invalid_error_type_raises_error(self):
        """
        Verify that an invalid error_type raises a ValueError.
        """
        logger = get_logger("test_invalid")
        
        with pytest.raises(ValueError) as exc_info:
            log_structured_error(logger, "invalid_error_type", {"key": "value"})
        
        assert "Invalid error_type" in str(exc_info.value)
        assert "unmatched_participant_ids" in str(exc_info.value)
        assert "image_processing_failures" in str(exc_info.value)

    def test_structured_json_format_compliance(self):
        """
        Verify that the logged JSON message contains all required fields
        as per the contract: error_type, timestamp, and details.
        """
        logger = get_logger("test_format")
        logger.handlers.clear()
        
        handler = logging.Handler()
        handler.setLevel(logging.ERROR)
        log_records = []
        
        def emit(record):
            log_records.append(record)
        
        handler.emit = emit
        logger.addHandler(handler)
        
        details = {"test_key": "test_value"}
        
        # Test both valid error types
        for error_type in ["unmatched_participant_ids", "image_processing_failures"]:
            log_structured_error(logger, error_type, details)
            
            assert len(log_records) == 1
            record = log_records[0]
            
            parsed_message = json.loads(record.getMessage())
            
            # Verify structure
            assert isinstance(parsed_message["error_type"], str)
            assert isinstance(parsed_message["timestamp"], str)
            assert isinstance(parsed_message["details"], dict)
            
            # Reset for next iteration
            log_records.clear()