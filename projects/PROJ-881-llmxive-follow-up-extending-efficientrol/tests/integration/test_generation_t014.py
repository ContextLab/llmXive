import json
import os
import sys
import tempfile
from pathlib import Path
import logging

import pytest

# Import the module to test
# Note: We assume the module is installed or in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.generation.generation import label_validity, setup_logging

class TestT014_NoMatchLogging:
    """
    Test T014: Exception handling for cases where no ground-truth path matches.
    - Verify WARNING log is emitted with correct JSON format.
    - Verify validity is False.
    """

    def test_no_match_logs_warning(self, tmp_path):
        """
        Test that label_validity logs a WARNING when no path matches.
        """
        # Setup logging to a file in tmp_path
        log_file = tmp_path / "test_generation.log"
        
        # Re-setup logger to use our temp file
        # We need to mock the logger or reconfigure it. 
        # Since setup_logging creates a global logger, we'll configure it directly here.
        logger = logging.getLogger("generation_logger")
        logger.handlers.clear() # Clear existing handlers
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "prompt_id": getattr(record, 'prompt_id', None),
                    "validity": getattr(record, 'validity', None),
                    "reason": getattr(record, 'reason', None)
                }
                return json.dumps(log_record)

        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Test data: Generated token that does NOT match any ground truth path
        # GT Path: [1, 2, 3]
        # Generated: [1, 99, 3] -> Index 1 (99) does not match 2
        generated_tokens = [1, 99, 3]
        prompt_id = "test-prompt-001"
        ground_truth_paths = [[1, 2, 3]]
        
        # Call the function
        is_valid, _ = label_validity(generated_tokens, prompt_id, ground_truth_paths, None)

        # Assertions
        assert is_valid == False, "Expected validity to be False when no match found"

        # Check log file
        assert log_file.exists(), "Log file should be created"
        
        log_content = log_file.read_text()
        log_lines = log_content.strip().split('\n')
        
        # Find the warning log entry
        warning_entry = None
        for line in log_lines:
            if line:
                entry = json.loads(line)
                if entry.get("reason") == "no_match":
                    warning_entry = entry
                    break

        assert warning_entry is not None, "Expected a 'no_match' log entry"
        assert warning_entry["prompt_id"] == prompt_id
        assert warning_entry["validity"] == False
        assert warning_entry["reason"] == "no_match"
        assert warning_entry["level"] == "WARNING"

    def test_match_does_not_log_warning(self, tmp_path):
        """
        Test that label_validity does NOT log a warning when a match is found.
        """
        log_file = tmp_path / "test_generation_match.log"
        
        logger = logging.getLogger("generation_logger")
        logger.handlers.clear()
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "prompt_id": getattr(record, 'prompt_id', None),
                    "validity": getattr(record, 'validity', None),
                    "reason": getattr(record, 'reason', None)
                }
                return json.dumps(log_record)

        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Test data: Generated token matches ground truth
        generated_tokens = [1, 2, 3]
        prompt_id = "test-prompt-002"
        ground_truth_paths = [[1, 2, 3]]
        
        is_valid, _ = label_validity(generated_tokens, prompt_id, ground_truth_paths, None)

        assert is_valid == True

        log_content = log_file.read_text()
        # Should be empty or not contain 'no_match'
        assert "no_match" not in log_content, "Should not log no_match when valid"

    def test_multiple_paths_any_match(self, tmp_path):
        """
        Test that if ANY path matches, validity is True and no warning is logged.
        """
        log_file = tmp_path / "test_generation_multi.log"
        
        logger = logging.getLogger("generation_logger")
        logger.handlers.clear()
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "prompt_id": getattr(record, 'prompt_id', None),
                    "validity": getattr(record, 'validity', None),
                    "reason": getattr(record, 'reason', None)
                }
                return json.dumps(log_record)

        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Path 1: [1, 2, 3]
        # Path 2: [1, 99, 3]
        # Generated: [1, 99, 3] -> Matches Path 2
        generated_tokens = [1, 99, 3]
        prompt_id = "test-prompt-003"
        ground_truth_paths = [[1, 2, 3], [1, 99, 3]]
        
        is_valid, _ = label_validity(generated_tokens, prompt_id, ground_truth_paths, None)

        assert is_valid == True, "Should be valid if ANY path matches"
        
        log_content = log_file.read_text()
        assert "no_match" not in log_content, "Should not log no_match if any path matches"