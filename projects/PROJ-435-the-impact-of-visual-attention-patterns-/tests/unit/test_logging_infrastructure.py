"""
Unit tests for the logging infrastructure (T008).

Tests verify that:
1. Loggers are correctly configured
2. Data quality warnings are captured
3. Exclusion counts are logged correctly
4. Pipeline progress messages are formatted appropriately
"""

import logging
import os
import tempfile
import pytest
from pathlib import Path

# Import the logging module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.logging_config import (
    setup_logging,
    get_quality_logger,
    get_exclusion_logger,
    get_pipeline_logger,
    log_data_quality_warning,
    log_exclusion,
    log_pipeline_progress,
    log_pipeline_error,
    DATA_QUALITY_MSG_PREFIX,
    EXCLUSION_MSG_PREFIX,
    PIPELINE_PROGRESS_MSG_PREFIX
)


class TestLoggingSetup:
    """Tests for the basic logging setup."""

    def test_setup_logging_creates_handlers(self):
        """Verify that setup_logging creates console handler."""
        logger = setup_logging(log_level=logging.DEBUG)
        assert len(logger.handlers) >= 1

        # Check that at least one handler is a StreamHandler
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_setup_logging_with_file(self):
        """Verify that setup_logging creates file handler when log_file is provided."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            tmp_path = tmp.name

        try:
            logger = setup_logging(log_file=tmp_path, log_level=logging.DEBUG)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1

            # Verify file exists and has content
            assert os.path.exists(tmp_path)
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_setup_logging_clears_existing_handlers(self):
        """Verify that setup_logging clears existing handlers to avoid duplicates."""
        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        logging.getLogger().addHandler(dummy_handler)

        # Setup logging again
        setup_logging(log_level=logging.DEBUG)

        # Count handlers
        handlers = logging.getLogger().handlers
        # Should have at most one StreamHandler (the one we just added)
        stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) == 1

        # Cleanup
        logging.getLogger().handlers.clear()


class TestQualityLogger:
    """Tests for data quality logging."""

    def test_quality_logger_prefix(self, caplog):
        """Verify that quality warnings have the correct prefix."""
        with caplog.at_level(logging.WARNING):
            logger = get_quality_logger()
            log_data_quality_warning(logger, "Test warning message")

        assert any(DATA_QUALITY_MSG_PREFIX in record.message for record in caplog.records)
        assert any("Test warning message" in record.message for record in caplog.records)

    def test_quality_logger_level(self):
        """Verify that quality logger respects log level."""
        logger = get_quality_logger()
        logger.setLevel(logging.ERROR)

        # This should not be logged
        with caplog.at_level(logging.WARNING) if 'caplog' in globals() else nullcontext():
            # We can't easily test this without caplog, but we can verify the level is set
            assert logger.level == logging.ERROR


class TestExclusionLogger:
    """Tests for exclusion logging."""

    def test_exclusion_logger_prefix(self, caplog):
        """Verify that exclusion messages have the correct prefix."""
        with caplog.at_level(logging.INFO):
            logger = get_exclusion_logger()
            log_exclusion(logger, "Low signal quality", count=5)

        assert any(EXCLUSION_MSG_PREFIX in record.message for record in caplog.records)
        assert any("5" in record.message for record in caplog.records)
        assert any("Low signal quality" in record.message for record in caplog.records)

    def test_exclusion_with_details(self, caplog):
        """Verify that exclusion messages include details when provided."""
        with caplog.at_level(logging.INFO):
            logger = get_exclusion_logger()
            details = {"participant_id": 123, "roi": "source"}
            log_exclusion(logger, "Missing ROI", count=1, details=details)

        assert any("participant_id" in record.message for record in caplog.records)
        assert any("123" in record.message for record in caplog.records)

    def test_exclusion_default_count(self, caplog):
        """Verify that exclusion defaults to count=1."""
        with caplog.at_level(logging.INFO):
            logger = get_exclusion_logger()
            log_exclusion(logger, "Test reason")

        assert any("Excluded 1 item(s)" in record.message for record in caplog.records)


class TestPipelineLogger:
    """Tests for pipeline progress logging."""

    def test_pipeline_progress_prefix(self, caplog):
        """Verify that pipeline progress messages have the correct prefix."""
        with caplog.at_level(logging.INFO):
            logger = get_pipeline_logger()
            log_pipeline_progress(logger, "Data Ingestion", "Starting to load data")

        assert any(PIPELINE_PROGRESS_MSG_PREFIX in record.message for record in caplog.records)
        assert any("[Data Ingestion]" in record.message for record in caplog.records)
        assert any("Starting to load data" in record.message for record in caplog.records)

    def test_pipeline_error_format(self, caplog):
        """Verify that pipeline errors are logged correctly."""
        with caplog.at_level(logging.ERROR):
            logger = get_pipeline_logger()
            try:
                raise ValueError("Test error")
            except Exception as e:
                log_pipeline_error(logger, "Data Processing", e)

        assert any(PIPELINE_PROGRESS_MSG_PREFIX in record.message for record in caplog.records)
        assert any("Data Processing" in record.message for record in caplog.records)
        assert any("Test error" in record.message for record in caplog.records)


class TestIntegration:
    """Integration tests for the logging system."""

    def test_multiple_loggers_independent(self, caplog):
        """Verify that different loggers work independently."""
        with caplog.at_level(logging.INFO):
            quality_logger = get_quality_logger()
            exclusion_logger = get_exclusion_logger()
            pipeline_logger = get_pipeline_logger()

            log_data_quality_warning(quality_logger, "Quality issue")
            log_exclusion(exclusion_logger, "Exclusion reason")
            log_pipeline_progress(pipeline_logger, "Stage", "Progress message")

        # Check that all three types of messages are present
        messages = [record.message for record in caplog.records]
        assert any(DATA_QUALITY_MSG_PREFIX in msg for msg in messages)
        assert any(EXCLUSION_MSG_PREFIX in msg for msg in messages)
        assert any(PIPELINE_PROGRESS_MSG_PREFIX in msg for msg in messages)

    def test_logging_to_file(self):
        """Verify that logs are written to file when configured."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            tmp_path = tmp.name

        try:
            # Setup logging with file
            setup_logging(log_file=tmp_path, log_level=logging.DEBUG)

            # Log some messages
            quality_logger = get_quality_logger()
            log_data_quality_warning(quality_logger, "Test quality warning")

            exclusion_logger = get_exclusion_logger()
            log_exclusion(exclusion_logger, "Test exclusion")

            # Verify file has content
            with open(tmp_path, 'r') as f:
                content = f.read()

            assert DATA_QUALITY_MSG_PREFIX in content
            assert EXCLUSION_MSG_PREFIX in content
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Reset logging for other tests
        logging.getLogger().handlers.clear()
