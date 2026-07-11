"""
Unit tests for code/utils/logger.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to adjust the import path based on how tests are run
# Assuming tests are run from project root: python -m pytest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.logger import (
    initialize_memory_log,
    log_memory_usage,
    log_timeout_error,
    log_generation_error,
    log_batch_reduction,
    get_memory_log,
    get_memory_log_path,
    _load_existing_logs,
    _save_logs
)

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for testing log files."""
    # Mock the LOG_FILE path to use a temporary directory
    with patch("utils.logger.PROJECT_ROOT", tmp_path):
        with patch("utils.logger.DATA_DIR", tmp_path / "data"):
            with patch("utils.logger.PROCESSED_DIR", tmp_path / "data" / "processed"):
                with patch("utils.logger.LOG_FILE", tmp_path / "data" / "processed" / "memory_log.json"):
                    yield tmp_path / "data" / "processed"

def test_initialize_memory_log_creates_file(temp_log_dir):
    """Test that initialize_memory_log creates the JSON file with initial entry."""
    log_path = initialize_memory_log()
    
    assert os.path.exists(log_path)
    
    with open(log_path, "r") as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["event"] == "log_initialization"
    assert "timestamp" in data[0]

def test_initialize_memory_log_resets_existing(temp_log_dir):
    """Test that initialize_memory_log overwrites existing log content."""
    # Create a fake log file
    log_path = temp_log_dir / "memory_log.json"
    with open(log_path, "w") as f:
        json.dump([{"event": "old_event"}], f)
    
    initialize_memory_log()
    
    with open(log_path, "r") as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["event"] == "log_initialization"

def test_log_memory_usage(temp_log_dir):
    """Test logging memory usage adds an entry."""
    initialize_memory_log()
    
    log_memory_usage(
        task_id="test_001",
        style="pep8",
        current_mb=1024.5,
        peak_mb=2048.0,
        batch_size=8,
        action="probe"
    )
    
    entries = get_memory_log()
    assert len(entries) == 2  # Init + new entry
    
    last_entry = entries[-1]
    assert last_entry["event"] == "memory_usage"
    assert last_entry["task_id"] == "test_001"
    assert last_entry["style"] == "pep8"
    assert last_entry["current_mb"] == 1024.5
    assert last_entry["peak_mb"] == 2048.0
    assert last_entry["batch_size"] == 8
    assert last_entry["action"] == "probe"

def test_log_timeout_error(temp_log_dir):
    """Test logging a timeout error."""
    initialize_memory_log()
    
    log_timeout_error(
        task_id="test_002",
        style="minified",
        timeout_seconds=300
    )
    
    entries = get_memory_log()
    last_entry = entries[-1]
    
    assert last_entry["event"] == "timeout_error"
    assert last_entry["task_id"] == "test_002"
    assert last_entry["action"] == "skipped"
    assert last_entry["timeout_seconds"] == 300

def test_log_generation_error(temp_log_dir):
    """Test logging a generation error."""
    initialize_memory_log()
    
    log_generation_error(
        task_id="test_003",
        style="neutral",
        error_type="AST_Parsing",
        message="Invalid syntax detected"
    )
    
    entries = get_memory_log()
    last_entry = entries[-1]
    
    assert last_entry["event"] == "generation_error"
    assert last_entry["error_type"] == "AST_Parsing"
    assert last_entry["message"] == "Invalid syntax detected"

def test_log_batch_reduction(temp_log_dir):
    """Test logging a batch size reduction."""
    initialize_memory_log()
    
    log_batch_reduction(
        task_id="test_004",
        old_size=16,
        new_size=8,
        reason="high_memory"
    )
    
    entries = get_memory_log()
    last_entry = entries[-1]
    
    assert last_entry["event"] == "batch_reduction"
    assert last_entry["old_batch_size"] == 16
    assert last_entry["new_batch_size"] == 8
    assert last_entry["reason"] == "high_memory"

def test_get_memory_log_path(temp_log_dir):
    """Test that get_memory_log_path returns the correct path."""
    log_path = initialize_memory_log()
    assert get_memory_log_path() == log_path

def test_save_and_load_logs(temp_log_dir):
    """Test internal save and load functions."""
    test_entries = [
        {"event": "test1", "data": 1},
        {"event": "test2", "data": 2}
    ]
    
    _save_logs(test_entries)
    loaded = _load_existing_logs()
    
    assert loaded == test_entries

def test_load_nonexistent_file(temp_log_dir):
    """Test loading from a non-existent file returns empty list."""
    # Ensure file doesn't exist
    log_file = temp_log_dir / "memory_log.json"
    if log_file.exists():
        log_file.unlink()
        
    result = _load_existing_logs()
    assert result == []

def test_load_invalid_json_returns_empty(temp_log_dir):
    """Test loading from a file with invalid JSON returns empty list."""
    log_file = temp_log_dir / "memory_log.json"
    with open(log_file, "w") as f:
        f.write("not valid json {{{")
        
    result = _load_existing_logs()
    assert result == []

def test_load_non_list_json_returns_empty(temp_log_dir):
    """Test loading from a file with valid JSON but not a list returns empty list."""
    log_file = temp_log_dir / "memory_log.json"
    with open(log_file, "w") as f:
        json.dump({"event": "single"}, f)
        
    result = _load_existing_logs()
    assert result == []