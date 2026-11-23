import pytest
import time
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.timing_logger import (
    setup_timing_logging,
    log_document_processing_time,
    measure_document_processing,
    run_timing_validation,
    TIMING_LOG_PATH
)
from code.config import RESULTS_DIR

@pytest.fixture
def clean_log_file(tmp_path, monkeypatch):
    """Fixture to ensure a clean log file for each test."""
    # Override the global path to a temporary file
    temp_log = tmp_path / "timing_logs.json"
    monkeypatch.setattr("code.timing_logger.TIMING_LOG_PATH", temp_log)
    return temp_log

def test_setup_timing_logging(clean_log_file):
    """Test that logging is configured and the file path exists."""
    logger = setup_timing_logging()
    assert logger is not None
    assert logger.level == logging.INFO

def test_log_document_processing_time_pass(clean_log_file):
    """Test logging a document that meets the 60s constraint."""
    log_document_processing_time("doc_123", 15.5)
    
    assert clean_log_file.exists()
    with open(clean_log_file, 'r') as f:
        content = f.read()
    
    entry = json.loads(content.strip())
    assert entry['doc_id'] == 'doc_123'
    assert entry['duration_seconds'] == 15.5
    assert entry['status'] == 'PASS'
    assert entry['threshold_seconds'] == 60.0

def test_log_document_processing_time_fail(clean_log_file):
    """Test logging a document that exceeds the 60s constraint."""
    log_document_processing_time("doc_456", 75.2)
    
    with open(clean_log_file, 'r') as f:
        entry = json.loads(f.read().strip())
    
    assert entry['status'] == 'FAIL'
    assert entry['duration_seconds'] == 75.2

def test_measure_document_processing_success(clean_log_file):
    """Test the wrapper measures time correctly for a successful function."""
    def mock_process(doc_id):
        time.sleep(0.1)
        return {"result": "ok"}
    
    result = measure_document_processing("doc_789", mock_process)
    assert result == {"result": "ok"}
    
    # Verify log was written
    with open(clean_log_file, 'r') as f:
        entry = json.loads(f.read().strip())
    assert entry['doc_id'] == 'doc_789'
    assert entry['status'] == 'PASS' # 0.1s < 60s

def test_measure_document_processing_failure(clean_log_file):
    """Test that the wrapper logs the duration even if the function raises."""
    def mock_fail(doc_id):
        time.sleep(0.05)
        raise ValueError("Simulated error")
    
    with pytest.raises(ValueError):
        measure_document_processing("doc_error", mock_fail)
    
    # Verify log was written despite error
    with open(clean_log_file, 'r') as f:
        entry = json.loads(f.read().strip())
    assert entry['doc_id'] == 'doc_error'
    assert entry['status'] == 'PASS' # 0.05s < 60s, error doesn't change duration status logic here

def test_run_timing_validation_empty(clean_log_file):
    """Test validation when no logs exist."""
    # Ensure file is empty
    if clean_log_file.exists():
        clean_log_file.unlink()
    
    summary = run_timing_validation()
    assert "error" in summary or summary.get("total_processed") == 0

def test_run_timing_validation_with_violations(clean_log_file):
    """Test validation logic with mixed pass/fail entries."""
    # Manually write logs
    with open(clean_log_file, 'w') as f:
        f.write(json.dumps({"doc_id": "d1", "duration_seconds": 10.0, "status": "PASS"}) + '\n')
        f.write(json.dumps({"doc_id": "d2", "duration_seconds": 100.0, "status": "FAIL"}) + '\n')
        f.write(json.dumps({"doc_id": "d3", "duration_seconds": 20.0, "status": "PASS"}) + '\n')
    
    summary = run_timing_validation()
    
    assert summary['total_processed'] == 3
    assert summary['violations'] == 1
    assert summary['constraint_met'] == False
    assert abs(summary['avg_duration'] - 43.33) < 0.1
    assert summary['max_duration'] == 100.0

def test_run_timing_validation_all_pass(clean_log_file):
    """Test validation when all entries pass."""
    with open(clean_log_file, 'w') as f:
        f.write(json.dumps({"doc_id": "d1", "duration_seconds": 10.0, "status": "PASS"}) + '\n')
        f.write(json.dumps({"doc_id": "d2", "duration_seconds": 50.0, "status": "PASS"}) + '\n')
    
    summary = run_timing_validation()
    assert summary['violations'] == 0
    assert summary['constraint_met'] == True

import logging