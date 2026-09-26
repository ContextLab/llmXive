"""
Unit tests for the logging infrastructure.
"""
import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_pipeline_logger,
    get_log_file_path,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    log_chunk_info,
    log_task_start,
    log_task_end,
    log_data_file_created
)


class TestLoggingInfrastructure:
    """Tests for the base logging infrastructure."""

    def test_get_pipeline_logger_returns_logger(self):
        """Test that get_pipeline_logger returns a valid logger instance."""
        logger = get_pipeline_logger("test_pipeline")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_pipeline"
        assert logger.level == logging.DEBUG

    def test_get_pipeline_logger_caches_instance(self):
        """Test that the same logger instance is returned on subsequent calls."""
        logger1 = get_pipeline_logger("test_cache")
        logger2 = get_pipeline_logger("test_cache")
        assert logger1 is logger2

    def test_get_log_file_path_returns_path(self):
        """Test that get_log_file_path returns a valid Path object."""
        log_path = get_log_file_path()
        assert isinstance(log_path, Path)
        assert log_path.exists()
        assert log_path.suffix == ".log"

    def test_log_pipeline_start_writes_to_log(self, caplog):
        """Test that log_pipeline_start writes appropriate messages."""
        with caplog.at_level(logging.INFO):
            log_pipeline_start("test_pipeline", {"key": "value"})

        assert any("PIPELINE START" in record.message for record in caplog.records)
        assert any("test_pipeline" in record.message for record in caplog.records)

    def test_log_pipeline_end_writes_to_log(self, caplog):
        """Test that log_pipeline_end writes appropriate messages."""
        with caplog.at_level(logging.INFO):
            log_pipeline_end("test_pipeline", success=True, duration_seconds=10.5)

        assert any("PIPELINE END" in record.message for record in caplog.records)
        assert any("SUCCESS" in record.message for record in caplog.records)
        assert any("10.5" in record.message for record in caplog.records)

    def test_log_error_captures_exception(self, caplog):
        """Test that log_error captures exception details."""
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error")
            except Exception as e:
                log_error(e, context="test_context")

        assert any("ValueError" in record.message for record in caplog.records)
        assert any("test_context" in record.message for record in caplog.records)

    def test_log_metric_writes_to_log(self, caplog):
        """Test that log_metric writes appropriate messages."""
        with caplog.at_level(logging.INFO):
            log_metric("accuracy", 0.95, stage="validation")

        assert any("METRIC" in record.message for record in caplog.records)
        assert any("accuracy" in record.message for record in caplog.records)
        assert any("0.95" in record.message for record in caplog.records)

    def test_log_chunk_info_writes_to_log(self, caplog):
        """Test that log_chunk_info writes progress information."""
        with caplog.at_level(logging.INFO):
            log_chunk_info(chunk_id=5, total_chunks=10, items_processed=500, stage="processing")

        assert any("CHUNK" in record.message for record in caplog.records)
        assert any("5/10" in record.message for record in caplog.records)
        assert any("500" in record.message for record in caplog.records)

    def test_log_task_start_writes_to_log(self, caplog):
        """Test that log_task_start writes task start messages."""
        with caplog.at_level(logging.INFO):
            log_task_start("T006", "Create logging infrastructure")

        assert any("TASK START" in record.message for record in caplog.records)
        assert any("T006" in record.message for record in caplog.records)

    def test_log_task_end_writes_to_log(self, caplog):
        """Test that log_task_end writes task end messages."""
        with caplog.at_level(logging.INFO):
            log_task_end("T006", "Create logging infrastructure", success=True, duration_seconds=2.5)

        assert any("TASK END" in record.message for record in caplog.records)
        assert any("SUCCESS" in record.message for record in caplog.records)

    def test_log_data_file_created_writes_to_log(self, caplog):
        """Test that log_data_file_created writes file creation messages."""
        with caplog.at_level(logging.INFO):
            log_data_file_created(
                filepath=Path("/data/test.csv"),
                size_bytes=1024000,
                record_count=1000
            )

        assert any("DATA FILE CREATED" in record.message for record in caplog.records)
        assert any("test.csv" in record.message for record in caplog.records)
        assert any("1000" in record.message for record in caplog.records)

    def test_logger_has_both_file_and_console_handlers(self):
        """Test that the logger has both file and console handlers."""
        logger = get_pipeline_logger("test_handlers")
        handlers = logger.handlers

        file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
        console_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]

        assert len(file_handlers) >= 1
        assert len(console_handlers) >= 1

    def test_log_file_is_created_in_output_directory(self):
        """Test that the log file is created in the expected output directory."""
        log_path = get_log_file_path()
        # Verify the path contains "output" or "logs" based on project structure
        assert "logs" in str(log_path) or "output" in str(log_path)
