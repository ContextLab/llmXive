"""
Tests for the runtime_monitor module.

These tests verify that the runtime monitoring functionality works correctly,
including start time recording, runtime measurement, and compliance checking.
"""
import os
import json
import time
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the module under test
from runtime_monitor import (
    setup_runtime_logger,
    record_start_time,
    load_pipeline_start_time,
    measure_and_log_runtime,
    main,
    MAX_RUNTIME_SECONDS,
    START_TIME_FILE,
    RUNTIME_LOG_FILE
)

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    # Create necessary directories
    data_dir = tmp_path / "data" / "processed"
    results_dir = tmp_path / "results"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Temporarily override the file paths
    original_start_file = START_TIME_FILE
    original_runtime_file = RUNTIME_LOG_FILE
    
    # Use monkeypatch-like behavior by changing the module's constants
    import runtime_monitor
    runtime_monitor.START_TIME_FILE = data_dir / "pipeline_start_time.json"
    runtime_monitor.RUNTIME_LOG_FILE = results_dir / "runtime.log"
    
    yield {
        "data_dir": data_dir,
        "results_dir": results_dir,
        "start_file": runtime_monitor.START_TIME_FILE,
        "runtime_file": runtime_monitor.RUNTIME_LOG_FILE
    }
    
    # Restore original paths
    runtime_monitor.START_TIME_FILE = original_start_file
    runtime_monitor.RUNTIME_LOG_FILE = original_runtime_file

def test_setup_runtime_logger():
    """Test that the logger is properly configured."""
    logger = setup_runtime_logger()
    assert logger is not None
    assert logger.name == "runtime_monitor"
    assert len(logger.handlers) > 0

def test_record_start_time(temp_dirs):
    """Test that start time is recorded correctly."""
    logger = setup_runtime_logger()
    start_time = record_start_time(logger)
    
    # Verify start time is a valid timestamp
    assert isinstance(start_time, float)
    assert start_time > 0
    
    # Verify file was created
    assert temp_dirs["start_file"].exists()
    
    # Verify file contents
    with open(temp_dirs["start_file"], 'r') as f:
        data = json.load(f)
    
    assert "start_timestamp" in data
    assert "start_datetime" in data
    assert abs(data["start_timestamp"] - start_time) < 1  # Within 1 second

def test_load_pipeline_start_time(temp_dirs):
    """Test loading the start time from file."""
    # First record a start time
    record_start_time()
    
    # Then load it
    loaded_time = load_pipeline_start_time()
    
    assert loaded_time is not None
    assert isinstance(loaded_time, float)

def test_load_pipeline_start_time_missing_file(temp_dirs):
    """Test loading when file doesn't exist."""
    loaded_time = load_pipeline_start_time()
    assert loaded_time is None

def test_measure_and_log_runtime_success(temp_dirs):
    """Test runtime measurement when within limit."""
    # Record start time
    record_start_time()
    
    # Simulate a short runtime (1 second)
    time.sleep(1)
    
    # Measure runtime
    success = measure_and_log_runtime()
    
    assert success is True
    
    # Verify log file was created
    assert temp_dirs["runtime_file"].exists()
    
    # Verify log contents
    with open(temp_dirs["runtime_file"], 'r') as f:
        content = f.read()
    
    assert "Pipeline Runtime Check" in content
    assert "Status: PASS" in content

def test_measure_and_log_runtime_failure(temp_dirs):
    """Test runtime measurement when exceeding limit."""
    # Record a start time from 7 hours ago
    old_start_time = time.time() - (7 * 3600)
    
    start_data = {
        "start_timestamp": old_start_time,
        "start_datetime": datetime.fromtimestamp(old_start_time).isoformat()
    }
    
    with open(temp_dirs["start_file"], 'w') as f:
        json.dump(start_data, f)
    
    # Measure runtime
    success = measure_and_log_runtime()
    
    assert success is False
    
    # Verify log file contains failure status
    with open(temp_dirs["runtime_file"], 'r') as f:
        content = f.read()
    
    assert "Status: FAIL" in content
    assert "Runtime violation" in content

def test_main_success(temp_dirs):
    """Test main function when runtime is within limit."""
    record_start_time()
    time.sleep(0.5)
    
    result = main()
    assert result == 0

def test_main_failure(temp_dirs):
    """Test main function when runtime exceeds limit."""
    # Record a start time from 7 hours ago
    old_start_time = time.time() - (7 * 3600)
    start_data = {
        "start_timestamp": old_start_time,
        "start_datetime": datetime.fromtimestamp(old_start_time).isoformat()
    }
    
    with open(temp_dirs["start_file"], 'w') as f:
        json.dump(start_data, f)
    
    result = main()
    assert result == 1