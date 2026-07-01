"""
Unit tests for the logging infrastructure.
"""
import os
import json
import tempfile
import logging
from pathlib import Path
import pytest

# Adjust path to include project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import (
    get_logger,
    log_provenance,
    log_processing_step,
    log_error,
    LOGS_DIR
)

class TestLoggerCreation:
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logging.Logger instance."""
        logger = get_logger("test_basic")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_basic"
    
    def test_get_logger_reuses_existing(self):
        """Test that calling get_logger twice returns the same instance."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")
        assert logger1 is logger2
    
    def test_logger_has_handlers(self):
        """Test that the logger has both console and file handlers."""
        logger = get_logger("test_handlers")
        assert len(logger.handlers) >= 2  # Console + File
    
    def test_log_file_created(self):
        """Test that log file is created in the logs directory."""
        logger = get_logger("test_file_creation", log_file="test_custom.log")
        log_path = LOGS_DIR / "test_custom.log"
        assert log_path.exists()

class TestProvenanceLogging:
    def test_log_provenance_creates_entry(self, caplog):
        """Test that log_provenance creates a valid JSON entry."""
        with caplog.at_level(logging.INFO):
            log_provenance(
                source="data/raw/test.csv",
                destination="data/processed/test_clean.csv",
                metadata={"checksum": "abc123", "rows": 100}
            )
        
        assert len(caplog.records) >= 1
        log_message = caplog.records[-1].message
        entry = json.loads(log_message)
        
        assert entry["source"] == "data/raw/test.csv"
        assert entry["destination"] == "data/processed/test_clean.csv"
        assert entry["metadata"]["checksum"] == "abc123"
        assert "timestamp" in entry

class TestProcessingStepLogging:
    def test_log_processing_step_creates_entry(self, caplog):
        """Test that log_processing_step logs inputs, outputs, and parameters."""
        with caplog.at_level(logging.INFO):
            log_processing_step(
                step_name="preprocess_test",
                input_files=["data/raw/input.csv"],
                output_files=["data/processed/output.csv"],
                parameters={"normalize": True, "threshold": 0.5}
            )
        
        # Should have at least 2 log entries (Starting step + JSON)
        json_logs = [r for r in caplog.records if r.message.startswith("{")]
        assert len(json_logs) >= 1
        
        entry = json.loads(json_logs[-1].message)
        assert entry["step"] == "preprocess_test"
        assert "data/raw/input.csv" in entry["inputs"]
        assert "data/processed/output.csv" in entry["outputs"]
        assert entry["parameters"]["normalize"] is True

class TestErrorLogging:
    def test_log_error_captures_exception(self, caplog):
        """Test that log_error captures exception type and message."""
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error message")
            except Exception as e:
                log_error("test_step", e, context={"param": "value"})
        
        error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_logs) >= 2  # Error message + JSON entry
        
        json_logs = [r for r in error_logs if r.message.startswith("{")]
        if json_logs:
            entry = json.loads(json_logs[-1].message)
            assert entry["error_type"] == "ValueError"
            assert "Test error message" in entry["error_message"]
            assert entry["context"]["param"] == "value"

class TestLoggerNamespaces:
    def test_different_namespaces_independent(self):
        """Test that different loggers maintain independent state."""
        logger1 = get_logger("namespace_a")
        logger2 = get_logger("namespace_b")
        
        assert logger1.name == "namespace_a"
        assert logger2.name == "namespace_b"
        assert logger1 is not logger2

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up log files after tests."""
    yield
    # Remove test-specific log files
    test_logs = [f for f in LOGS_DIR.glob("test_*.log")]
    for log in test_logs:
        log.unlink(missing_ok=True)