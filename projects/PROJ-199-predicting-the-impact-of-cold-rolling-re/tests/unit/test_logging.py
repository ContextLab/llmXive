"""
Unit tests for the logging infrastructure.
"""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from code.utils.logging import (
    LineageAdapter,
    configure_lineage,
    get_logger,
    setup_logging,
)


class TestSetupLogging:
    def test_setup_logging_creates_file_handler(self, tmp_path):
        """Verify that setup_logging creates a file handler."""
        log_file = str(tmp_path / "test.log")
        setup_logging(log_file=log_file, enable_console=False)

        root_logger = logging.getLogger()
        file_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename == log_file

    def test_setup_logging_creates_console_handler(self):
        """Verify that setup_logging creates a console handler when enabled."""
        setup_logging(enable_console=True)
        root_logger = logging.getLogger()
        console_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) >= 1  # At least one

    def test_setup_logging_clears_existing_handlers(self):
        """Verify that setup_logging clears existing handlers to prevent duplicates."""
        root_logger = logging.getLogger()
        initial_count = len(root_logger.handlers)

        setup_logging(enable_console=False)

        # Should have exactly one handler (file) after setup
        file_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        # Total handlers should be 1 (file)
        assert len(root_logger.handlers) == 1


class TestGetLogger:
    def test_get_logger_returns_named_logger(self):
        """Verify that get_logger returns a logger with the correct name."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"

    def test_get_logger_caches_logger_instance(self):
        """Verify that get_logger returns the same instance for the same name."""
        logger1 = get_logger("cached.module")
        logger2 = get_logger("cached.module")
        assert logger1 is logger2

    def test_get_logger_with_lineage_returns_adapter(self):
        """Verify that get_logger returns a LineageAdapter when context is provided."""
        logger = get_logger(
            "test.lineage", sample_id="S001", step="download", reduction=20.0
        )
        assert isinstance(logger, LineageAdapter)

    def test_get_logger_with_lineage_injects_extra(self):
        """Verify that LineageAdapter injects context into log records."""
        logger = get_logger(
            "test.inject", sample_id="S002", step="preprocess", reduction=40.0
        )

        # Capture the log record
        with patch.object(logger.logger, "handle") as mock_handle:
            logger.info("Test message")
            assert mock_handle.called
            record = mock_handle.call_args[0][0]
            assert record.extra.get("sample_id") == "S002"
            assert record.extra.get("step") == "preprocess"
            assert record.extra.get("reduction") == 40.0


class TestLineageAdapter:
    def test_process_injects_extra(self):
        """Verify that LineageAdapter.process injects context into kwargs."""
        adapter = LineageAdapter(
            logging.getLogger("base"),
            {"sample_id": "X", "step": "Y", "reduction": 10},
        )

        msg, kwargs = adapter.process("Message", {})
        assert kwargs["extra"]["sample_id"] == "X"
        assert kwargs["extra"]["step"] == "Y"
        assert kwargs["extra"]["reduction"] == 10

    def test_process_preserves_existing_extra(self):
        """Verify that LineageAdapter.process merges with existing extra."""
        adapter = LineageAdapter(
            logging.getLogger("base"),
            {"sample_id": "A", "step": "B"},
        )

        msg, kwargs = adapter.process("Message", {"extra": {"custom": "value"}})
        assert kwargs["extra"]["sample_id"] == "A"
        assert kwargs["extra"]["custom"] == "value"


class TestConfigureLineage:
    def test_configure_lineage_returns_adapter(self):
        """Verify that configure_lineage returns a LineageAdapter."""
        logger = configure_lineage(
            "test.configure", sample_id="Z", step="validate"
        )
        assert isinstance(logger, LineageAdapter)

    def test_configure_lineage_sets_correct_context(self):
        """Verify that configure_lineage sets the correct context."""
        logger = configure_lineage(
            "test.context",
            sample_id="C123",
            step="train",
            reduction=50.5,
        )
        assert logger.extra["sample_id"] == "C123"
        assert logger.extra["step"] == "train"
        assert logger.extra["reduction"] == 50.5
