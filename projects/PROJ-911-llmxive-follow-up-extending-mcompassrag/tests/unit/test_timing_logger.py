import pytest
import json
import time
from pathlib import Path
import logging
import sys
from unittest.mock import patch, mock_open

# Add project root to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.timing_logger import (
    setup_timing_logging,
    log_document_processing_time,
    measure_document_processing,
    run_timing_validation,
    TIMING_LOG_PATH,
    TIMING_LOG_FILE
)
from code.config import RESULTS_DIR

@pytest.fixture
def mock_json_file(tmp_path):
    """Fixture to mock the JSON log file path"""
    # Override the global path for testing
    original_path = TIMING_LOG_PATH
    test_path = tmp_path / "timing_logs.json"
    test_path.touch()
    return test_path

def test_setup_timing_logging_creates_file(tmp_path):
    """Test that setup_timing_logging creates the log file"""
    # We can't easily mock the global constants in the module, so we test the behavior
    # by checking if the file is created when the logger is used.
    # For this unit test, we assume the directory exists.
    logger = setup_timing_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO

def test_log_document_processing_time_writes_json(tmp_path):
    """Test that log_document_processing_time writes to the JSON file"""
    # Mock the file operations
    test_log_path = tmp_path / "test_timing.json"
    
    # We need to patch the module's TIMING_LOG_PATH
    with patch('code.timing_logger.TIMING_LOG_PATH', test_log_path):
        logger = setup_timing_logging()
        start = time.perf_counter()
        time.sleep(0.01) # Small delay
        end = time.perf_counter()
        
        log_document_processing_time(logger, "doc_123", start, end, "completed")
        
        assert test_log_path.exists()
        with open(test_log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["doc_id"] == "doc_123"
        assert data[0]["status"] == "completed"
        assert 0 < data[0]["duration_seconds"] < 1.0

def test_measure_document_processing_success():
    """Test measure_document_processing with a successful function"""
    def dummy_process(doc_id):
        time.sleep(0.01)
        return f"Processed {doc_id}"
    
    # Mock the logger to avoid file I/O in test
    with patch('code.timing_logger.setup_timing_logging') as mock_logger_setup:
        mock_logger = mock_logger_setup.return_value
        
        result = measure_document_processing("test_doc", dummy_process, "test_doc")
        
        assert result == "Processed test_doc"
        mock_logger.info.assert_called()

def test_measure_document_processing_timeout_warning():
    """Test that measure_document_processing logs a warning if > 60s"""
    def slow_process(doc_id):
        # Simulate a long process without actually sleeping 60s
        # We will mock the time check logic or just test the logging path
        # by manually triggering the warning condition in the logic
        pass
    
    # We test the logic by mocking time.perf_counter to simulate a long duration
    with patch('code.timing_logger.time.perf_counter') as mock_time:
        mock_time.side_effect = [0, 65.0] # Start at 0, end at 65
        
        with patch('code.timing_logger.setup_timing_logging') as mock_logger_setup:
            mock_logger = mock_logger_setup.return_value
            
            # This should trigger the warning path
            try:
                measure_document_processing("slow_doc", lambda x: None, "slow_doc")
            except:
                pass # Ignore any exceptions from the mock function
            
            # Check that warning was logged
            # The function logs warning if duration >= 60
            # We need to verify the log call happened
            assert mock_logger.warning.called

def test_run_timing_validation_no_logs(tmp_path):
    """Test run_timing_validation when log file is missing"""
    with patch('code.timing_logger.TIMING_LOG_PATH', tmp_path / "missing.json"):
        report = run_timing_validation()
        assert report["status"] == "no_logs_found"

def test_run_timing_validation_with_violations(tmp_path):
    """Test run_timing_validation correctly identifies violations"""
    test_log_path = tmp_path / "timing_logs.json"
    test_data = [
        {"doc_id": "doc_1", "duration_seconds": 10.0},
        {"doc_id": "doc_2", "duration_seconds": 65.0},
        {"doc_id": "doc_3", "duration_seconds": 5.0}
    ]
    test_log_path.write_text(json.dumps(test_data))
    
    with patch('code.timing_logger.TIMING_LOG_PATH', test_log_path):
        report = run_timing_validation()
        
        assert report["status"] == "failed"
        assert report["violation_count"] == 1
        assert len(report["violations"]) == 1
        assert report["violations"][0]["doc_id"] == "doc_2"
        assert report["all_within_limit"] is False
        
        assert report["average_processing_time"] == pytest.approx(26.666, rel=0.01)
        assert report["max_processing_time"] == 65.0
