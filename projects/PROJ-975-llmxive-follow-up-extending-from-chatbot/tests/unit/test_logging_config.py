"""
Unit tests for code/logging_config.py (Task T007).
"""
import os
import json
import tempfile
import shutil
import pytest
from code.logging_config import CSVLogHandler, get_logger, log_experiment_entry, verify_log_file_exists

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_csv_handler_creates_file(temp_log_dir):
    """Test that CSVLogHandler creates the file and writes a header."""
    filepath = os.path.join(temp_log_dir, "test_log.csv")
    handler = CSVLogHandler(filepath)
    
    # Log a message to trigger file creation
    handler.emit(logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    ))
    
    assert os.path.exists(filepath)
    with open(filepath, 'r') as f:
        header = f.readline().strip()
        assert "timestamp" in header
        assert "level" in header
        assert "message" in header
        assert "metadata_json" in header

def test_get_logger_writes_to_file(temp_log_dir):
    """Test that get_logger writes entries to the specified file."""
    # Monkeypatch the LOG_FILE_PATH for this test
    import code.logging_config as lc
    original_path = lc.LOG_FILE_PATH
    lc.LOG_FILE_PATH = os.path.join(temp_log_dir, "test_logger.csv")
    
    try:
        logger = get_logger("test_logger")
        logger.info("Test log entry")
        
        assert verify_log_file_exists()
        with open(lc.LOG_FILE_PATH, 'r') as f:
            content = f.read()
            assert "Test log entry" in content
    finally:
        lc.LOG_FILE_PATH = original_path

def test_log_experiment_entry_structure(temp_log_dir):
    """Test that log_experiment_entry writes correct metadata structure."""
    import code.logging_config as lc
    original_path = lc.LOG_FILE_PATH
    lc.LOG_FILE_PATH = os.path.join(temp_log_dir, "test_entry.csv")
    
    try:
        log_experiment_entry(
            task_id="T001",
            success=True,
            latency=0.5,
            tokens=100,
            retrieval_precision=0.8,
            retrieval_diversity=0.2,
            pruning_risk_count=0,
            library_size=50,
            pruning_enabled=False
        )
        
        assert verify_log_file_exists()
        with open(lc.LOG_FILE_PATH, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1  # Header + 1 entry
            
            # Parse the last line as CSV to verify structure
            import csv
            reader = csv.DictReader(lines)
            row = next(reader)
            
            assert json.loads(row["metadata_json"])["task_id"] == "T001"
            assert json.loads(row["metadata_json"])["success"] is True
            assert json.loads(row["metadata_json"])["library_size"] == 50
    finally:
        lc.LOG_FILE_PATH = original_path

def test_verify_log_file_exists_false():
    """Test verify_log_file_exists returns False for non-existent file."""
    import code.logging_config as lc
    original_path = lc.LOG_FILE_PATH
    lc.LOG_FILE_PATH = "/non/existent/path/file.csv"
    
    try:
        assert not verify_log_file_exists()
    finally:
        lc.LOG_FILE_PATH = original_path
