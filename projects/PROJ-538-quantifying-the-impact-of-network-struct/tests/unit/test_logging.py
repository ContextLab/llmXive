import pytest
import json
import os
from pathlib import Path
from code.utils import log_audit_event, get_logger, AUDIT_LOG_PATH, DATA_DIR

@pytest.fixture
def clean_audit_log():
    """Ensure audit log is clean before and after test."""
    if AUDIT_LOG_PATH.exists():
        AUDIT_LOG_PATH.unlink()
    yield
    if AUDIT_LOG_PATH.exists():
        AUDIT_LOG_PATH.unlink()

def test_audit_log_creation(clean_audit_log):
    """Test that log_audit_event creates the file and writes valid JSON."""
    assert not AUDIT_LOG_PATH.exists()

    details = {"test_key": "test_value", "count": 42}
    log_audit_event("TEST_EVENT", details, "INFO")

    assert AUDIT_LOG_PATH.exists()

    with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    assert content != ""
    
    # Parse as JSON Lines
    lines = content.splitlines()
    assert len(lines) == 1
    
    entry = json.loads(lines[0])
    assert entry["event_type"] == "TEST_EVENT"
    assert entry["status"] == "INFO"
    assert entry["details"]["test_key"] == "test_value"
    assert "timestamp" in entry

def test_audit_log_append(clean_audit_log):
    """Test that multiple events are appended correctly."""
    log_audit_event("EVENT_1", {"id": 1})
    log_audit_event("EVENT_2", {"id": 2})

    with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.read().strip().splitlines()

    assert len(lines) == 2

    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])

    assert entry1["event_type"] == "EVENT_1"
    assert entry2["event_type"] == "EVENT_2"
    assert entry1["details"]["id"] == 1
    assert entry2["details"]["id"] == 2

def test_logger_output(clean_audit_log, caplog):
    """Test that the logger outputs to console."""
    logger = get_logger("test_logger")
    
    # caplog captures the log output
    with caplog.at_level("INFO"):
        log_audit_event("CONSOLE_TEST", {"msg": "hello"})
    
    assert "CONSOLE_TEST" in caplog.text
    assert "INFO" in caplog.text
