import pytest
import json
import logging
import os
from pathlib import Path
import sys

# Add code to path if running standalone
if "code" not in sys.path:
    sys.path.insert(0, "code")

from utils.logging_config import (
    setup_logging,
    log_subject_exclusion,
    log_memory_usage,
    get_exclusion_summary,
    ExclusionFormatter,
    MemoryFormatter,
    LOG_DIR,
    EXCLUSION_LOG_FILE_NAME,
    MEMORY_LOG_FILE_NAME,
)

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up log files before and after each test."""
    # Clean before
    if LOG_DIR.exists():
        for f in LOG_DIR.glob("*.log"):
            f.unlink()
        for f in LOG_DIR.glob("*.jsonl"):
            f.unlink()
    
    yield
    
    # Clean after
    if LOG_DIR.exists():
        for f in LOG_DIR.glob("*.log"):
            f.unlink()
        for f in LOG_DIR.glob("*.jsonl"):
            f.unlink()

def test_setup_logging_creates_handlers():
    """Test that setup_logging creates the expected handlers."""
    logger = setup_logging()
    assert logger is not None
    assert len(logger.handlers) >= 2  # Console + File + Exclusion + Memory (at least 2)

def test_log_subject_exclusion_writes_jsonl():
    """Test that log_subject_exclusion writes to the exclusion JSONL file."""
    setup_logging()
    logger = logging.getLogger("llmXive")
    
    log_subject_exclusion("sub-test", "Test exclusion", {"key": "value"}, logger)
    
    exclusion_file = LOG_DIR / EXCLUSION_LOG_FILE_NAME
    assert exclusion_file.exists(), "Exclusion log file should be created"
    
    with open(exclusion_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["subject_id"] == "sub-test"
    assert data["reason"] == "Test exclusion"
    assert data["details"]["key"] == "value"

def test_log_memory_usage_writes_jsonl():
    """Test that log_memory_usage writes to the memory JSONL file."""
    setup_logging()
    logger = logging.getLogger("llmXive")
    
    log_memory_usage(100.0, 200.0, 7000.0, "test_action", logger)
    
    memory_file = LOG_DIR / MEMORY_LOG_FILE_NAME
    assert memory_file.exists(), "Memory log file should be created"
    
    with open(memory_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["current_rss_mb"] == 100.0
    assert data["peak_rss_mb"] == 200.0
    assert data["limit_mb"] == 7000.0
    assert data["action"] == "test_action"

def test_get_exclusion_summary_counts_reasons():
    """Test that get_exclusion_summary correctly counts exclusion reasons."""
    setup_logging()
    logger = logging.getLogger("llmXive")
    
    log_subject_exclusion("sub-1", "Motion", {}, logger)
    log_subject_exclusion("sub-2", "Motion", {}, logger)
    log_subject_exclusion("sub-3", "Missing Data", {}, logger)
    
    summary = get_exclusion_summary(logger)
    
    assert summary["Motion"] == 2
    assert summary["Missing Data"] == 1

def test_exclusion_formatter_format():
    """Test the ExclusionFormatter format method."""
    formatter = ExclusionFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.subject_id = "sub-1"
    record.reason = "Reason"
    record.details = {"k": "v"}
    
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["subject_id"] == "sub-1"
    assert data["reason"] == "Reason"
    assert data["details"]["k"] == "v"

def test_memory_formatter_format():
    """Test the MemoryFormatter format method."""
    formatter = MemoryFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.current_rss_mb = 100.0
    record.peak_rss_mb = 200.0
    record.limit_mb = 7000.0
    record.action = "check"
    
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["current_rss_mb"] == 100.0
    assert data["peak_rss_mb"] == 200.0
    assert data["action"] == "check"