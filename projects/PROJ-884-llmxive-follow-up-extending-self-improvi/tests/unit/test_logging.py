import os
import json
import pytest
from pathlib import Path
import time

# Import the function directly from the code package
from code import log_experiment_entry, setup_logging, LOG_FILE_PATH

@pytest.fixture(autouse=True)
def setup_log_file(tmp_path, monkeypatch):
    """
    Fixture to redirect LOG_FILE_PATH to a temporary directory for testing.
    """
    # Create a temp directory structure mimicking the project
    temp_processed = tmp_path / "data" / "processed"
    temp_processed.mkdir(parents=True)
    
    # Monkeypatch the LOG_FILE_PATH in the code module
    # We need to modify the module object's attribute
    import code
    original_path = code.LOG_FILE_PATH
    code.LOG_FILE_PATH = temp_processed / "test_experiment.log"
    
    yield code.LOG_FILE_PATH
    
    # Restore original path
    code.LOG_FILE_PATH = original_path

def test_setup_logging_creates_file(setup_log_file):
    """Test that setup_logging ensures the log file exists."""
    # Remove the file if it exists (in case of previous runs in same session)
    if setup_log_file.exists():
        setup_log_file.unlink()
    
    setup_logging()
    assert setup_log_file.exists()

def test_log_entry_structure(setup_log_file):
    """Test that log entries are valid JSON with required fields."""
    setup_logging()
    log_experiment_entry()
    
    with open(setup_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
    
    assert line.strip() != ""
    entry = json.loads(line)
    
    assert "timestamp" in entry
    assert "wall_clock" in entry
    assert "resource_usage" in entry
    
    # Check resource_usage structure
    assert "user_time" in entry["resource_usage"]
    assert "system_time" in entry["resource_usage"]
    assert "max_rss_kb" in entry["resource_usage"]
    
    # Validate types
    assert isinstance(entry["timestamp"], str)
    assert isinstance(entry["wall_clock"], float)
    assert isinstance(entry["resource_usage"], dict)
    assert isinstance(entry["resource_usage"]["user_time"], float)
    assert isinstance(entry["resource_usage"]["system_time"], float)
    assert isinstance(entry["resource_usage"]["max_rss_kb"], int)

def test_log_appends_new_lines(setup_log_file):
    """Test that multiple calls append new lines rather than overwriting."""
    setup_logging()
    
    time.sleep(0.01) # Ensure slight time difference
    log_experiment_entry()
    time.sleep(0.01)
    log_experiment_entry()
    
    with open(setup_log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    
    # Verify both are valid JSON
    for line in lines:
        json.loads(line)

def test_log_file_path_is_correct(setup_log_file):
    """Test that the log file is written to the expected location."""
    # The fixture already redirects to tmp_path, so we just check existence
    assert setup_log_file.parent.exists()
    assert setup_log_file.exists()