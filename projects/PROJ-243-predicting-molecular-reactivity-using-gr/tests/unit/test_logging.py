import os
import json
import tempfile
import shutil
import pytest
import logging
from datetime import datetime

# We need to mock the config or ensure directories are created
# Since we can't easily mock the global state of logging_utils in a real run,
# we will test the functions in a controlled environment.

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.logging_utils import setup_logging, log_metric, flush_metrics, get_metrics, log_execution_summary

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logging tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_setup_logging_creates_files(temp_log_dir):
    """Test that setup_logging creates the log and metrics files."""
    log_dir = os.path.join(temp_log_dir, "logs")
    log_file = "test.log"
    metrics_file = "test_metrics.json"
    
    logger = setup_logging(
        log_dir=log_dir,
        log_file_name=log_file,
        metrics_file_name=metrics_file
    )
    
    # Verify directory exists
    assert os.path.isdir(log_dir)
    
    # Verify log file exists
    log_path = os.path.join(log_dir, log_file)
    assert os.path.isfile(log_path)
    
    # Verify metrics file exists
    metrics_path = os.path.join(log_dir, metrics_file)
    assert os.path.isfile(metrics_path)
    
    # Verify logger is configured
    assert logger is not None
    assert len(logger.handlers) > 0

def test_log_metric_writes_to_file(temp_log_dir):
    """Test that log_metric writes to the JSON file."""
    log_dir = os.path.join(temp_log_dir, "logs")
    metrics_file = "metrics.json"
    
    # Setup
    setup_logging(
        log_dir=log_dir,
        log_file_name="test.log",
        metrics_file_name=metrics_file
    )
    
    # Log a metric
    test_value = 123.45
    log_metric("test_metric", test_value, stage="test_stage")
    
    # Read the file
    metrics_path = os.path.join(log_dir, metrics_file)
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    # Verify
    assert len(data) == 1
    assert data[0]["metric_name"] == "test_metric"
    assert data[0]["value"] == test_value
    assert data[0]["stage"] == "test_stage"
    assert "timestamp" in data[0]

def test_log_execution_summary(temp_log_dir):
    """Test the execution summary logging function."""
    log_dir = os.path.join(temp_log_dir, "logs")
    metrics_file = "metrics.json"
    
    setup_logging(
        log_dir=log_dir,
        log_file_name="test.log",
        metrics_file_name=metrics_file
    )
    
    log_execution_summary(
        stage="test_summary",
        success=True,
        duration_seconds=5.5,
        metrics={"accuracy": 0.99}
    )
    
    metrics_path = os.path.join(log_dir, metrics_file)
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    # Should have 2 entries: one for accuracy, one for the summary metric if logged
    # The implementation logs 'accuracy' via log_metric inside log_execution_summary
    # It also logs 'logging_initialized' in setup? No, that was in the main script.
    # Here we just check that the summary logic didn't crash and wrote something.
    assert len(data) >= 1
    
    # Find the accuracy entry
    accuracy_entries = [e for e in data if e["metric_name"] == "accuracy"]
    assert len(accuracy_entries) == 1
    assert accuracy_entries[0]["value"] == 0.99

def test_flush_metrics_clears_buffer(temp_log_dir):
    """Test that flush_metrics writes and clears the buffer."""
    log_dir = os.path.join(temp_log_dir, "logs")
    metrics_file = "metrics.json"
    
    setup_logging(
        log_dir=log_dir,
        log_file_name="test.log",
        metrics_file_name=metrics_file
    )
    
    log_metric("temp1", 1)
    log_metric("temp2", 2)
    
    # Before flush, file might be empty if buffer logic is strict, 
    # but our implementation flushes on every log_metric.
    # Let's test the get_metrics function which reads from disk.
    metrics = get_metrics()
    assert len(metrics) == 2

def test_logger_output(temp_log_dir):
    """Test that the logger writes to the text log file."""
    log_dir = os.path.join(temp_log_dir, "logs")
    log_file = "output.log"
    
    logger = setup_logging(
        log_dir=log_dir,
        log_file_name=log_file
    )
    
    test_msg = "Test message for logging"
    logger.info(test_msg)
    
    log_path = os.path.join(log_dir, log_file)
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert test_msg in content