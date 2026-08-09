import pytest
import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.timing_logger import (
    setup_timing_logging,
    log_document_processing_time,
    measure_document_processing,
    run_timing_validation,
    TIMING_LOG_PATH
)
from code.config import RESULTS_DIR

@pytest.fixture
def clean_timing_log(tmp_path):
    """Fixture to ensure a clean log file for integration tests"""
    # Create a temporary log file path
    test_log = tmp_path / "integration_timing_logs.json"
    # Initialize empty
    test_log.write_text("[]")
    return test_log

def test_full_timing_pipeline(tmp_path, clean_timing_log):
    """
    Integration test: Simulate processing a small batch of documents,
    log their times, and validate the results.
    """
    # Patch the global path to use our temp file
    with patch('code.timing_logger.TIMING_LOG_PATH', clean_timing_log):
        logger = setup_timing_logging()
        
        # Simulate processing 3 documents
        docs = ["doc_A", "doc_B", "doc_C"]
        times = []
        
        for doc in docs:
            start = time.perf_counter()
            # Simulate work
            time.sleep(0.01)
            end = time.perf_counter()
            
            log_document_processing_time(logger, doc, start, end, "completed")
            times.append(end - start)
        
        # Validate the log file
        assert clean_timing_log.exists()
        with open(clean_timing_log, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 3
        log_doc_ids = [l["doc_id"] for l in logs]
        assert set(log_doc_ids) == set(docs)
        
        # Run validation
        with patch('code.timing_logger.TIMING_LOG_PATH', clean_timing_log):
            report = run_timing_validation()
        
        assert report["status"] == "passed"
        assert report["total_documents"] == 3
        assert report["all_within_limit"] is True

def test_timing_validation_fails_on_timeout(tmp_path, clean_timing_log):
    """
    Integration test: Verify that a document taking > 60s causes validation to fail.
    """
    with patch('code.timing_logger.TIMING_LOG_PATH', clean_timing_log):
        logger = setup_timing_logging()
        
        # Simulate a fast doc
        start = time.perf_counter()
        time.sleep(0.01)
        end = time.perf_counter()
        log_document_processing_time(logger, "fast_doc", start, end, "completed")
        
        # Simulate a slow doc (manually craft the log entry to avoid 60s sleep)
        log_entry = {
            "doc_id": "slow_doc",
            "start_time": 0,
            "end_time": 65.0,
            "duration_seconds": 65.0,
            "status": "timeout_warning",
            "details": {}
        }
        
        # Append manually
        logs = [log_entry]
        with open(clean_timing_log, 'w') as f:
            json.dump(logs, f)
        
        # Validate
        with patch('code.timing_logger.TIMING_LOG_PATH', clean_timing_log):
            report = run_timing_validation()
        
        assert report["status"] == "failed"
        assert report["violation_count"] == 1
        assert report["all_within_limit"] is False

from unittest.mock import patch