"""
Unit tests for the logging_config module.
"""
import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Import the module under test
import code.logging_config as logging_config

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    # Patch the LOG_DIR constant
    original_dir = logging_config.LOG_DIR
    logging_config.LOG_DIR = temp_dir
    yield temp_dir
    # Cleanup
    logging_config.LOG_DIR = original_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_ensure_log_dirs(temp_log_dir):
    """Test that the log directory is created if it doesn't exist."""
    # Remove the directory to test creation
    if os.path.exists(temp_log_dir):
        shutil.rmtree(temp_log_dir)
    
    logging_config._ensure_log_dirs()
    assert os.path.isdir(temp_log_dir)

def test_get_comparison_log_path(temp_log_dir):
    """Test the path generation for comparison log."""
    path = logging_config.get_comparison_log_path()
    expected = os.path.join(temp_log_dir, "comparison_log.json")
    assert path == expected

def test_get_resource_log_path(temp_log_dir):
    """Test the path generation for resource log."""
    path = logging_config.get_resource_log_path()
    expected = os.path.join(temp_log_dir, "resource_log.json")
    assert path == expected

def test_log_pairwise_comparison(temp_log_dir):
    """Test logging a pairwise comparison entry."""
    # Clear any existing file
    log_path = logging_config.get_comparison_log_path()
    if os.path.exists(log_path):
        os.remove(log_path)
    
    # Log an entry
    logging_config.log_pairwise_comparison(
        pair_id="test_pair_1",
        doc1_id="doc_A",
        doc2_id="doc_B",
        cosine_sim=0.98,
        is_wasted=True
    )
    
    # Verify file exists and content
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    entry = json.loads(lines[0])
    
    assert entry["pair_id"] == "test_pair_1"
    assert entry["doc1_id"] == "doc_A"
    assert entry["doc2_id"] == "doc_B"
    assert entry["cosine_sim"] == 0.98
    assert entry["is_wasted"] is True
    assert "timestamp" in entry
    # Validate timestamp format
    datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))

def test_log_pairwise_comparison_multiple(temp_log_dir):
    """Test logging multiple entries appends correctly."""
    log_path = logging_config.get_comparison_log_path()
    if os.path.exists(log_path):
        os.remove(log_path)
    
    for i in range(3):
        logging_config.log_pairwise_comparison(
            pair_id=f"pair_{i}",
            doc1_id=f"doc_{i}",
            doc2_id=f"doc_{i+10}",
            cosine_sim=0.5 + i * 0.1,
            is_wasted=False
        )
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 3
    for i, line in enumerate(lines):
        entry = json.loads(line)
        assert entry["pair_id"] == f"pair_{i}"

def test_resource_monitoring_start_stop(temp_log_dir):
    """Test starting and stopping resource monitoring."""
    # Start monitoring
    logging_config.start_resource_monitoring(interval=0.1)
    
    # Wait a bit for data collection
    import time
    time.sleep(0.3)
    
    # Stop monitoring
    result_path = logging_config.stop_resource_monitoring()
    
    assert result_path is not None
    assert os.path.exists(result_path)
    
    with open(result_path, 'r') as f:
        logs = json.load(f)
    
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    # Check structure of a log entry
    entry = logs[0]
    assert "timestamp" in entry
    assert "pid" in entry
    assert "cpu_percent" in entry
    assert "memory_rss_mb" in entry
    assert "memory_vms_mb" in entry
    assert "thread_count" in entry

def test_init_logging(temp_log_dir):
    """Test initialization of logging."""
    # This should not raise and should set up the logger
    logging_config.init_logging()
    assert logging_config.logger is not None
    assert logging_config.logger.level == logging.INFO
