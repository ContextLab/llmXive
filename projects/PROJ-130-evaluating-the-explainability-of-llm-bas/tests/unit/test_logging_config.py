"""
Unit tests for the logging configuration module.

These tests verify that:
1. The logger initializes correctly
2. Edge cases are logged to both console and file
3. Error counts are accurately tallied
4. Convenience methods work as expected
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to temporarily redirect the STATE_DIR for testing
# so we don't pollute the actual project state directory
@pytest.fixture
def temp_state_dir():
    """Create a temporary directory to act as the state directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_path = Path(__file__).parent.parent.parent / "state"
        # Mock the path module to use our temp directory
        with patch("utils.logging_config.STATE_DIR", Path(tmpdir)):
            with patch("utils.logging_config.ERROR_LOG_PATH", Path(tmpdir) / "error_log.json"):
                # Reset the global logger to ensure clean state
                import utils.logging_config
                utils.logging_config._edge_logger = None
                yield Path(tmpdir)

def test_logger_initialization(temp_state_dir):
    """Test that the logger initializes and creates the log file."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH

    logger = get_edge_logger()
    assert logger is not None
    assert ERROR_LOG_PATH.exists()

def test_log_edge_case_to_file(temp_state_dir):
    """Test that an edge case is written to the JSON log file."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH

    logger = get_edge_logger()
    logger.log_edge_case(
        error_code="E001",
        message="Test edge case",
        bug_id="test-bug-1",
        details={"test_key": "test_value"}
    )

    assert ERROR_LOG_PATH.exists()
    with open(ERROR_LOG_PATH, "r") as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["error_code"] == "E001"
    assert entry["message"] == "Test edge case"
    assert entry["bug_id"] == "test-bug-1"
    assert entry["details"]["test_key"] == "test_value"

def test_log_invalid_patch(temp_state_dir):
    """Test the convenience method for invalid patches."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH, ERROR_CODES

    logger = get_edge_logger()
    logger.log_invalid_patch(bug_id="bug-123", reason="Syntax error in diff")

    with open(ERROR_LOG_PATH, "r") as f:
        entry = json.loads(f.readline())

    assert entry["error_code"] == ERROR_CODES["INVALID_PATCH"]
    assert entry["bug_id"] == "bug-123"
    assert "Syntax error" in entry["message"]
    assert entry["details"]["reason"] == "Syntax error in diff"

def test_log_timeout(temp_state_dir):
    """Test the convenience method for timeouts."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH, ERROR_CODES

    logger = get_edge_logger()
    logger.log_timeout(bug_id="bug-456", operation="patch_generation", timeout_seconds=30.0)

    with open(ERROR_LOG_PATH, "r") as f:
        entry = json.loads(f.readline())

    assert entry["error_code"] == ERROR_CODES["GENERATION_TIMEOUT"]
    assert entry["bug_id"] == "bug-456"
    assert entry["details"]["operation"] == "patch_generation"
    assert entry["details"]["timeout_seconds"] == 30.0

def test_log_missing_rationale(temp_state_dir):
    """Test the convenience method for missing rationales."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH, ERROR_CODES

    logger = get_edge_logger()
    logger.log_missing_rationale(bug_id="bug-789", expected_path="/fake/path.txt")

    with open(ERROR_LOG_PATH, "r") as f:
        entry = json.loads(f.readline())

    assert entry["error_code"] == ERROR_CODES["MISSING_RATIONALE"]
    assert entry["bug_id"] == "bug-789"
    assert entry["details"]["expected_path"] == "/fake/path.txt"

def test_get_error_counts(temp_state_dir):
    """Test that error counts are accurately tallied."""
    from utils.logging_config import get_edge_logger, get_error_counts, ERROR_CODES

    logger = get_edge_logger()
    logger.log_invalid_patch(bug_id="bug-1", reason="Error 1")
    logger.log_invalid_patch(bug_id="bug-2", reason="Error 2")
    logger.log_timeout(bug_id="bug-3", operation="gen", timeout_seconds=10)

    counts = get_error_counts()
    assert counts[ERROR_CODES["INVALID_PATCH"]] == 2
    assert counts[ERROR_CODES["GENERATION_TIMEOUT"]] == 1
    # All other codes should be 0
    for code, count in counts.items():
        if code not in [ERROR_CODES["INVALID_PATCH"], ERROR_CODES["GENERATION_TIMEOUT"]]:
            assert count == 0

def test_empty_log_file_returns_zero_counts(temp_state_dir):
    """Test that an empty log file returns all zero counts."""
    from utils.logging_config import get_error_counts, ERROR_CODES

    counts = get_error_counts()
    for code, count in counts.items():
        assert count == 0

def test_multiple_log_entries(temp_state_dir):
    """Test that multiple entries are appended correctly."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH

    logger = get_edge_logger()
    for i in range(5):
        logger.log_edge_case(
            error_code="E001",
            message=f"Message {i}",
            bug_id=f"bug-{i}"
        )

    with open(ERROR_LOG_PATH, "r") as f:
        lines = f.readlines()
    assert len(lines) == 5

def test_invalid_error_code_fallback(temp_state_dir):
    """Test that an invalid error code falls back to CONFIGURATION_ERROR."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH, ERROR_CODES

    logger = get_edge_logger()
    # Pass an invalid error code
    logger.log_edge_case(
        error_code="INVALID_CODE",
        message="Test"
    )

    with open(ERROR_LOG_PATH, "r") as f:
        entry = json.loads(f.readline())

    assert entry["error_code"] == ERROR_CODES["CONFIGURATION_ERROR"]

def test_log_name_mapping(temp_state_dir):
    """Test that error code names (e.g., 'INVALID_PATCH') are mapped to codes."""
    from utils.logging_config import get_edge_logger, ERROR_LOG_PATH, ERROR_CODES

    logger = get_edge_logger()
    # Pass the name instead of the code
    logger.log_edge_case(
        error_code="INVALID_PATCH",
        message="Test"
    )

    with open(ERROR_LOG_PATH, "r") as f:
        entry = json.loads(f.readline())

    assert entry["error_code"] == ERROR_CODES["INVALID_PATCH"]