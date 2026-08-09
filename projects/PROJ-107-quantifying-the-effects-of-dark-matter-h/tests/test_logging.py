import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Ensure imports work from test directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_pipeline_logger,
    get_log_file_path,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    log_chunk_info
)
from utils.config import get_project_root

class TestLoggingInfrastructure:
    """Tests for the base logging infrastructure (Task T006)"""

    def test_get_pipeline_logger_creation(self):
        """Test that a logger is created and configured correctly"""
        logger = get_pipeline_logger("test_creation")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_creation"
        assert logger.level == logging.INFO
        # Should have at least console and file handlers
        assert len(logger.handlers) >= 1

    def test_get_pipeline_logger_singleton(self):
        """Test that calling get_pipeline_logger twice returns the same instance"""
        logger1 = get_pipeline_logger("test_singleton")
        logger2 = get_pipeline_logger("test_singleton")
        assert logger1 is logger2

    def test_log_file_path_exists(self):
        """Test that a log file is created and path is retrievable"""
        logger = get_pipeline_logger("test_path")
        log_path = get_log_file_path("test_path")
        
        assert log_path is not None
        assert log_path.exists()
        assert log_path.suffix == ".log"

    def test_log_pipeline_start(self):
        """Test pipeline start logging"""
        logger = get_pipeline_logger("test_start")
        # Should not raise
        log_pipeline_start(logger, task_id="T006")
        
        # Verify log file was written to
        log_path = get_log_file_path("test_start")
        assert log_path.exists()
        content = log_path.read_text()
        assert "Pipeline execution started" in content
        assert "T006" in content

    def test_log_pipeline_end(self):
        """Test pipeline end logging"""
        logger = get_pipeline_logger("test_end")
        log_pipeline_end(logger, success=True)
        
        log_path = get_log_file_path("test_end")
        content = log_path.read_text()
        assert "SUCCESS" in content

    def test_log_error(self):
        """Test error logging"""
        logger = get_pipeline_logger("test_error")
        try:
            1 / 0
        except ZeroDivisionError as e:
            log_error(logger, e, context={"test": "value"})
        
        log_path = get_log_file_path("test_error")
        content = log_path.read_text()
        assert "ZeroDivisionError" in content
        assert "test=value" in content

    def test_log_metric(self):
        """Test metric logging"""
        logger = get_pipeline_logger("test_metric")
        log_metric(logger, "accuracy", 0.95, "percent")
        
        log_path = get_log_file_path("test_metric")
        content = log_path.read_text()
        assert "accuracy" in content
        assert "0.95" in content
        assert "percent" in content

    def test_log_chunk_info(self):
        """Test chunk info logging"""
        logger = get_pipeline_logger("test_chunk")
        log_chunk_info(logger, chunk_id=0, total_chunks=10, items_in_chunk=100, elapsed=0.5)
        
        log_path = get_log_file_path("test_chunk")
        content = log_path.read_text()
        assert "Chunk 1/10" in content
        assert "100" in content
        assert "0.50" in content

    def test_log_produced_in_project_logs_dir(self):
        """Test that logs are written to the project's logs directory"""
        logger = get_pipeline_logger("test_location")
        log_path = get_log_file_path("test_location")
        project_root = get_project_root()
        
        # The log file should be under project_root/logs
        assert log_path.is_relative_to(project_root / "logs")
        assert log_path.parent.name == "logs"
