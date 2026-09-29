import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    log_chunk_info,
    log_task_start,
    log_task_end,
    log_data_file_created,
    get_log_file_path
)
from utils.config import get_project_root, get_logs_path

class TestLoggingInfrastructure:
    """Tests for the base logging infrastructure."""

    def test_logger_creation_and_handlers(self):
        """Verify logger is created with correct handlers and levels."""
        logger = get_pipeline_logger("test_logger")
        
        assert logger is not None
        assert len(logger.handlers) == 2  # File and Console
        
        # Check handler levels
        levels = [h.level for h in logger.handlers]
        assert logging.DEBUG in levels
        assert logging.INFO in levels

    def test_log_file_creation(self):
        """Verify log files are created in the correct directory."""
        logger = get_pipeline_logger("test_file_log")
        # Force a log write to ensure file creation
        logger.info("Test message to trigger file creation")
        
        log_path = get_log_file_path("test_file_log")
        assert log_path.exists()
        assert log_path.suffix == ".log"

    def test_log_pipeline_start(self, caplog):
        """Test pipeline start logging."""
        with caplog.at_level(logging.INFO):
            log_pipeline_start("T006", {"seed": 42})
        
        assert "Pipeline execution started" in caplog.text
        assert "T006" in caplog.text

    def test_log_pipeline_end(self, caplog):
        """Test pipeline end logging."""
        with caplog.at_level(logging.INFO):
            log_pipeline_end("T006", "SUCCESS")
        
        assert "Pipeline execution ended" in caplog.text
        assert "SUCCESS" in caplog.text

    def test_log_error_with_exception(self, caplog):
        """Test error logging with exception details."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            with caplog.at_level(logging.ERROR):
                log_error("Something went wrong", e)
        
        assert "Something went wrong" in caplog.text
        assert "Test error" in caplog.text
        assert "ValueError" in caplog.text

    def test_log_metric(self, caplog):
        """Test metric logging."""
        with caplog.at_level(logging.INFO):
            log_metric("accuracy", 0.95, "evaluation")
        
        assert "Metric" in caplog.text
        assert "accuracy" in caplog.text
        assert "0.95" in caplog.text
        assert "[evaluation]" in caplog.text

    def test_log_chunk_info(self, caplog):
        """Test chunk progress logging."""
        with caplog.at_level(logging.INFO):
            log_chunk_info(1, 10, 1000)
        
        assert "chunk 2/10" in caplog.text
        assert "1000 items" in caplog.text

    def test_log_task_start_end(self, caplog):
        """Test task start and end logging."""
        with caplog.at_level(logging.INFO):
            log_task_start("data_ingestion")
            log_task_end("data_ingestion", 12.5)
        
        assert "Starting task" in caplog.text
        assert "data_ingestion" in caplog.text
        assert "Completed task" in caplog.text
        assert "12.50s" in caplog.text

    def test_log_data_file_created(self, caplog):
        """Test data file creation logging."""
        with caplog.at_level(logging.INFO):
            log_data_file_created("/data/processed/test.csv", 10.5)
        
        assert "Data file created" in caplog.text
        assert "test.csv" in caplog.text
        assert "10.50 MB" in caplog.text

    def test_logger_singleton_behavior(self):
        """Verify that getting the same logger twice returns the same instance."""
        logger1 = get_pipeline_logger("singleton_test")
        logger2 = get_pipeline_logger("singleton_test")
        
        assert logger1 is logger2
        assert len(logger1.handlers) == len(logger2.handlers)
        # Should not have duplicated handlers
        assert len(logger1.handlers) == 2
