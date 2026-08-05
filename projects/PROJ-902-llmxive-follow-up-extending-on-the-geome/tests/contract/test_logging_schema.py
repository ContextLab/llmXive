"""
Contract test for logging output schema.

Validates that the logging utility (src/utils/logging.py) produces
JSON-line logs where each line is a valid JSON object containing
the required schema fields: level, timestamp, message, and optional context.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logging import setup_logger, get_logger

REQUIRED_FIELDS = {"level", "timestamp", "message"}
OPTIONAL_FIELDS = {"context", "extra"}

def test_logger_produces_valid_json_lines(tmp_path: Path) -> None:
    """
    Contract test: Verify that the logger writes valid JSON lines
    to a file, and that each line conforms to the expected schema.
    """
    log_file = tmp_path / "test_log.jsonl"
    
    # Setup logger to write to our temp file
    logger = setup_logger(log_file=log_file, level="INFO")
    
    # Log a few messages
    logger.info("Test info message")
    logger.warning("Test warning message", extra={"key": "value"})
    logger.error("Test error message", exc_info=False)
    
    # Verify file exists and is not empty
    assert log_file.exists(), "Log file was not created"
    assert log_file.stat().st_size > 0, "Log file is empty"
    
    # Read and validate each line
    line_count = 0
    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Must be valid JSON
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {line_num} is not valid JSON: {e}")
            
            # Must be a dict
            assert isinstance(entry, dict), f"Line {line_num} is not a JSON object"
            
            # Check required fields
            missing = REQUIRED_FIELDS - set(entry.keys())
            assert not missing, f"Line {line_num} missing required fields: {missing}"
            
            # Validate field types
            assert isinstance(entry["level"], str), f"Line {line_num}: 'level' must be string"
            assert isinstance(entry["timestamp"], str), f"Line {line_num}: 'timestamp' must be string"
            assert isinstance(entry["message"], str), f"Line {line_num}: 'message' must be string"
            
            # Validate 'extra' if present
            if "extra" in entry:
                assert isinstance(entry["extra"], dict), f"Line {line_num}: 'extra' must be object"
            
            line_count += 1
    
    assert line_count > 0, "No valid log entries were found"

def test_logger_level_filtering(tmp_path: Path) -> None:
    """
    Contract test: Verify that the logger respects the configured level.
    """
    log_file = tmp_path / "test_level_filter.jsonl"
    logger = setup_logger(log_file=log_file, level="WARNING")
    
    logger.debug("This should not appear")
    logger.info("This should not appear")
    logger.warning("This should appear")
    logger.error("This should appear")
    
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "This should not appear" not in content
    assert "This should appear" in content

def test_logger_context_serialization(tmp_path: Path) -> None:
    """
    Contract test: Verify that complex context objects are serialized correctly.
    """
    log_file = tmp_path / "test_context.jsonl"
    logger = setup_logger(log_file=log_file, level="INFO")
    
    context = {
        "user_id": 12345,
        "items": [1, 2, 3],
        "metadata": {"nested": True, "value": 42.5}
    }
    
    logger.info("Context test", extra=context)
    
    with open(log_file, "r", encoding="utf-8") as f:
        line = f.readline().strip()
    
    entry = json.loads(line)
    assert "extra" in entry
    assert entry["extra"] == context