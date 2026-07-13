"""
Unit tests for the structured logging utility.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logger import (
    write_log_entry,
    write_log_entries,
    read_log_entries,
    get_log_stats,
    init_log_file,
)

@pytest.fixture
def temp_log_path():
    """Create a temporary file path for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        path = f.name
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)
    # Ensure parent dir cleanup if empty (optional, but good practice)
    parent = Path(path).parent
    if parent != Path(tempfile.gettempdir()):
        try:
            parent.rmdir()
        except OSError:
            pass

def test_write_single_entry(temp_log_path):
    """Test writing a single log entry."""
    entry = {"task_id": "T005", "status": "started", "agent": "baseline"}
    write_log_entry(temp_log_path, entry)
    
    entries = read_log_entries(temp_log_path)
    assert len(entries) == 1
    assert entries[0]["task_id"] == "T005"
    assert entries[0]["status"] == "started"
    assert "timestamp" in entries[0]

def test_write_multiple_entries(temp_log_path):
    """Test writing multiple log entries."""
    entries_data = [
        {"task_id": "T005", "step": 1},
        {"task_id": "T005", "step": 2},
        {"task_id": "T005", "step": 3},
    ]
    write_log_entries(temp_log_path, entries_data)
    
    entries = read_log_entries(temp_log_path)
    assert len(entries) == 3
    for i, entry in enumerate(entries):
        assert entry["step"] == i + 1
        assert "timestamp" in entry

def test_read_nonexistent_file():
    """Test reading from a file that doesn't exist."""
    path = "/tmp/nonexistent_log_file_12345.jsonl"
    entries = read_log_entries(path)
    assert entries == []

def test_get_log_stats_empty(temp_log_path):
    """Test stats on a newly created file."""
    init_log_file(temp_log_path)
    stats = get_log_stats(temp_log_path)
    assert stats["count"] == 0
    assert stats["size_bytes"] == 0

def test_get_log_stats_with_entries(temp_log_path):
    """Test stats after writing entries."""
    entry = {"test": "value"}
    write_log_entry(temp_log_path, entry)
    
    stats = get_log_stats(temp_log_path)
    assert stats["count"] == 1
    assert stats["size_bytes"] > 0
    assert stats["path"] == temp_log_path

def test_malformed_json_handling(temp_log_path):
    """Test that malformed JSON lines are skipped gracefully."""
    # Write valid entry
    write_log_entry(temp_log_path, {"valid": True})
    
    # Manually append a malformed line to simulate corruption
    with open(temp_log_path, "a") as f:
        f.write("{ this is not valid json }\n")
    
    # Write another valid entry
    write_log_entry(temp_log_path, {"valid": True, "second": True})
    
    entries = read_log_entries(temp_log_path)
    # Should have 2 valid entries, skipping the malformed one
    assert len(entries) == 2
    assert entries[0]["valid"] is True
    assert entries[1]["second"] is True

def test_init_creates_directory(temp_log_path):
    """Test that init_log_file creates parent directories."""
    deep_path = os.path.join(tempfile.gettempdir(), "llmxive_test", "subdir", "log.jsonl")
    try:
        init_log_file(deep_path)
        assert os.path.exists(deep_path)
    finally:
        # Cleanup
        if os.path.exists(deep_path):
            os.remove(deep_path)
        parent = Path(deep_path).parent
        try:
            parent.rmdir()
            parent.parent.rmdir()
        except OSError:
            pass