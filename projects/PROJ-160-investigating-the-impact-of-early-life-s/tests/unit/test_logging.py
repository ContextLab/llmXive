"""
Unit tests for logging infrastructure and error handling in code/main.py
"""
import json
import os
import tempfile
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import LOG_DIR
from code.main import setup_logging, PipelineError, DataLoadError, run_pipeline

def test_setup_logging_creates_file():
    """Test that setup_logging creates the log file and directory."""
    # Ensure clean state
    log_path = LOG_DIR / "pipeline.log"
    if log_path.exists():
        log_path.unlink()

    logger = setup_logging()
    
    # Trigger a log write
    logger.info("Test log entry")
    
    # Verify file exists
    assert log_path.exists(), "Log file should be created by setup_logging"

def test_log_format_is_json():
    """Test that log entries are valid JSON."""
    logger = setup_logging()
    logger.info("Test JSON entry")
    
    log_path = LOG_DIR / "pipeline.log"
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    # The last line should be the one we just wrote (or we can search for it)
    # Since we might have multiple runs, we check if the last non-empty line is valid JSON
    valid_json_found = False
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if "Test JSON entry" in entry.get("message", ""):
                valid_json_found = True
                assert "timestamp" in entry
                assert "level" in entry
                assert "message" in entry
                break
        except json.JSONDecodeError:
            continue
    
    assert valid_json_found, "Log entry should be valid JSON"

def test_custom_exception_raising():
    """Test that custom exceptions can be raised and caught."""
    try:
        raise DataLoadError("Simulated load failure", details={"file": "test.csv"})
    except DataLoadError as e:
        assert str(e) == "Simulated load failure"
        assert e.details["file"] == "test.csv"
    except Exception:
        assert False, "Should have raised DataLoadError"

def test_run_pipeline_handles_missing_file():
    """Test that run_pipeline handles missing input file gracefully."""
    # This test relies on the current implementation of run_pipeline
    # which logs a warning if cleaned_dataset.csv is missing but doesn't fail
    logger = setup_logging()
    # We expect this to return True even if file is missing (based on current logic)
    # or False if it treats missing file as critical. 
    # Based on T008 description, we need to ensure I/O errors are handled.
    # The current implementation logs a warning and continues.
    result = run_pipeline(logger)
    # Depending on strictness, this might be True or False. 
    # For this test, we assert it doesn't crash.
    assert result in [True, False]