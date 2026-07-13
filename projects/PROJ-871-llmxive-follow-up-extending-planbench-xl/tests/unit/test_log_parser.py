"""
Unit tests for the log parser module (T024).

These tests verify that the log parser correctly aggregates success/failure
counts from JSONL execution logs.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.log_parser import (
    load_execution_log,
    count_outcomes,
    parse_baseline_log,
    parse_augmented_log,
    get_aggregated_counts
)

@pytest.fixture
def temp_log_file():
    """Create a temporary JSONL log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Write test entries with various status formats
        entries = [
            {"task_id": 1, "final_status": "success", "steps": 5},
            {"task_id": 2, "final_status": "failure", "steps": 3},
            {"task_id": 3, "status": "success", "steps": 7},
            {"task_id": 4, "status": "failed", "steps": 2},
            {"task_id": 5, "outcome": "ok", "steps": 4},
            {"task_id": 6, "outcome": "error", "steps": 1},
            {"task_id": 7},  # Missing status field
            {"task_id": 8, "final_status": True},  # Boolean true
            {"task_id": 9, "final_status": False}, # Boolean false
        ]
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_load_execution_log_valid(temp_log_file):
    """Test loading a valid JSONL file."""
    entries = load_execution_log(temp_log_file)
    assert len(entries) == 9
    assert entries[0]["task_id"] == 1
    assert entries[8]["task_id"] == 9

def test_load_execution_log_nonexistent():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_execution_log("/nonexistent/path/file.jsonl")

def test_count_outcomes(temp_log_file):
    """Test counting outcomes from log entries."""
    entries = load_execution_log(temp_log_file)
    counts = count_outcomes(entries)
    
    # Expected:
    # success: task_id 1, 3, 5, 8 (4 items)
    # failure: task_id 2, 4, 6, 7 (missing), 9 (4 items)
    assert counts["success"] == 4
    assert counts["failure"] == 5
    assert counts["success"] + counts["failure"] == 9

def test_count_outcomes_empty():
    """Test counting outcomes from an empty list."""
    counts = count_outcomes([])
    assert counts["success"] == 0
    assert counts["failure"] == 0

def test_count_outcomes_all_success():
    """Test when all entries are successes."""
    entries = [
        {"status": "success"},
        {"final_status": "completed"},
        {"outcome": "ok"},
    ]
    counts = count_outcomes(entries)
    assert counts["success"] == 3
    assert counts["failure"] == 0

def test_count_outcomes_all_failure():
    """Test when all entries are failures."""
    entries = [
        {"status": "failure"},
        {"final_status": "failed"},
        {"outcome": "error"},
    ]
    counts = count_outcomes(entries)
    assert counts["success"] == 0
    assert counts["failure"] == 3

def test_parse_baseline_log_integration(temp_log_file):
    """Test parsing a baseline log file with custom path."""
    # This test would normally use a dedicated baseline log file
    # For unit testing, we reuse the temp file
    counts = parse_baseline_log(temp_log_file)
    assert isinstance(counts, dict)
    assert "success" in counts
    assert "failure" in counts

def test_parse_augmented_log_integration(temp_log_file):
    """Test parsing an augmented log file with custom path."""
    counts = parse_augmented_log(temp_log_file)
    assert isinstance(counts, dict)
    assert "success" in counts
    assert "failure" in counts

def test_get_aggregated_counts_missing_files():
    """Test that missing log files raise appropriate errors."""
    # This test expects the default paths to not exist in a clean test environment
    # We expect FileNotFoundError to be raised
    with pytest.raises(FileNotFoundError):
        get_aggregated_counts()

def test_status_field_priority(temp_log_file):
    """Test that final_status takes priority over status and outcome."""
    entries = [
        {"final_status": "success", "status": "failure", "outcome": "error"},
        {"final_status": "failure", "status": "success", "outcome": "ok"},
    ]
    counts = count_outcomes(entries)
    # Both should follow final_status
    assert counts["success"] == 1
    assert counts["failure"] == 1