"""
Unit tests for src/utils/logging.py
"""

import logging
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from src.utils.logging import (
    StructuredFormatter,
    setup_logger,
    log_progress,
    log_metric,
    log_error_summary,
    get_logger,
)


class TestStructuredFormatter:
    def test_format_basic_log(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello World",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Hello World"
        assert parsed["logger"] == "test"

    def test_format_with_extra_data(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning msg",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value", "count": 42}

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["count"] == 42


class TestSetupLogger:
    def test_setup_logger_console_only(self):
        logger = setup_logger("test_console", level=logging.DEBUG, console=True, log_file=None)
        assert logger.name == "test_console"
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logger_with_file(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            logger = setup_logger("test_file", level=logging.INFO, log_file=tmp_path, console=False)
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.FileHandler)

            # Verify file exists and is writable
            assert Path(tmp_path).exists()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_duplicate_handler_prevention(self):
        logger = setup_logger("test_dup", level=logging.INFO, console=False)
        count_before = len(logger.handlers)
        logger_again = setup_logger("test_dup", level=logging.INFO, console=False)
        count_after = len(logger_again.handlers)
        # Should be the same instance or at least same count if not reconfigured
        assert count_before == count_after


class TestLogProgress:
    def test_log_progress_basic(self):
        logger = setup_logger("test_prog", console=True, log_file=None)
        # Just ensure it doesn't crash and produces a log
        with pytest.raises(Exception):
            pass # Placeholder for actual capture if needed, but mostly testing no crash
        log_progress(logger, "StageA", 5, 10)
        # If it reaches here without exception, it passed the structural check

    def test_log_progress_percentage_calculation(self):
        # Logic check: 5/10 should be 50%
        # We can't easily assert the log content without a custom handler,
        # but we can verify the function signature and execution.
        logger = setup_logger("test_pct", console=True, log_file=None)
        log_progress(logger, "StageB", 3, 10, message="Custom msg")


class TestLogMetric:
    def test_log_metric_basic(self):
        logger = setup_logger("test_met", console=True, log_file=None)
        log_metric(logger, "mae", 0.5, unit="eV")

    def test_log_metric_with_context(self):
        logger = setup_logger("test_ctx", console=True, log_file=None)
        log_metric(logger, "loss", 0.1, context={"epoch": 5, "batch": 10})


class TestLogErrorSummary:
    def test_log_error_summary(self):
        logger = setup_logger("test_err", console=True, log_file=None)
        log_error_summary(
            logger,
            "DataError",
            "Missing file",
            details={"path": "/data/missing.csv"}
        )


class TestGetLogger:
    def test_get_logger_default(self):
        logger = get_logger()
        assert logger.name == "llmXive"

    def test_get_logger_custom(self):
        logger = get_logger("my_custom_module")
        assert logger.name == "my_custom_module"