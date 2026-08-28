"""
Unit tests for code/utils/logging.py
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
# Assuming the project root is the current working directory for tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import (
    StructuredJsonFormatter,
    setup_logging,
    log_result_artifact,
    log_error_summary,
    LOG_DIR
)


class TestStructuredJsonFormatter:
    def test_format_basic_log(self):
        formatter = StructuredJsonFormatter(task_id="TEST-001")
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Hello World",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["task_id"] == "TEST-001"
        assert data["message"] == "Hello World"
        assert "timestamp" in data

    def test_format_with_exception(self):
        formatter = StructuredJsonFormatter(task_id="TEST-002")
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Something failed",
            args=(),
            exc_info=exc_info
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]


class TestSetupLogging:
    def test_setup_logging_creates_handlers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(task_id="TEST-003", log_file=log_file)

            # Should have console and file handlers
            assert len(logger.handlers) == 2
            
            # Verify file handler exists
            file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
            assert file_handler is not None
            assert file_handler.baseFilename == log_file

    def test_setup_logging_clears_existing_handlers(self):
        logger = logging.getLogger()
        initial_count = len(logger.handlers)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(task_id="TEST-004", log_file=log_file)
            
            # Should have exactly 2 handlers (console + file) regardless of initial count
            assert len(logger.handlers) == 2


class TestLogResultArtifact:
    def test_log_result_artifact_creates_valid_json(self, caplog):
        # Setup logger with JSON formatter
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(task_id="TEST-005", log_file=log_file)
            
            log_result_artifact(
                logger,
                "data/processed/sample.csv",
                "csv",
                checksum="def456",
                size_bytes=2048,
                metadata={"rows": 100}
            )
            
            # Read the log file and verify JSON structure
            with open(log_file, "r") as f:
                lines = f.readlines()
                # Last line should be our log
                last_line = lines[-1]
                data = json.loads(last_line)
                
                assert data["event"] == "artifact_generated"
                assert data["artifact"]["path"] == "data/processed/sample.csv"
                assert data["artifact"]["checksum"] == "def456"
                assert data["artifact"]["size_bytes"] == 2048
                assert data["artifact"]["metadata"]["rows"] == 100


class TestLogErrorSummary:
    def test_log_error_summary_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(task_id="TEST-006", log_file=log_file)
            
            log_error_summary(
                logger,
                "FileNotFoundError",
                "Missing input file",
                details={"file": "data/raw/missing.csv"}
            )
            
            with open(log_file, "r") as f:
                lines = f.readlines()
                last_line = lines[-1]
                data = json.loads(last_line)
                
                assert data["event"] == "error_summary"
                assert data["error_type"] == "FileNotFoundError"
                assert data["message"] == "Missing input file"
                assert data["details"]["file"] == "data/raw/missing.csv"
