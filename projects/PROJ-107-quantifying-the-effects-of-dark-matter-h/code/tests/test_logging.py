"""
Unit tests for the logging infrastructure (Task T006).

Tests verify:
- Logger initialization and configuration
- Log file creation and path resolution
- Correctness of all logging helper functions
- Proper handling of errors and metrics
"""
import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys
import time

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
    log_data_file_created,
    _configure_logger
)
from utils.config import get_project_root


class TestLoggingInfrastructure:
    """Tests for the logging infrastructure."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset logger state for clean tests
        self.logger = None
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config to use temp dir
        self.original_get_logs_path = None
        if 'utils.config' in sys.modules:
            import utils.config
            self.original_get_logs_path = utils.config.get_logs_path
            
            def mock_get_logs_path():
                return Path(self.temp_dir)
            
            utils.config.get_logs_path = mock_get_logs_path
        
        # Reconfigure logger to use temp dir
        if 'utils.logging' in sys.modules:
            import utils.logging
            utils.logging._logger_instance = None
            utils.logging._log_file_path = None

    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original config
        if self.original_get_logs_path and 'utils.config' in sys.modules:
            import utils.config
            utils.config.get_logs_path = self.original_get_logs_path
        
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Reset logger state
        if 'utils.logging' in sys.modules:
            import utils.logging
            utils.logging._logger_instance = None
            utils.logging._log_file_path = None

    def test_logger_initialization(self):
        """Test that logger initializes correctly."""
        logger = get_pipeline_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive_pipeline"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2  # File and Stream handlers

    def test_log_file_creation(self):
        """Test that log file is created in the correct location."""
        logger = get_pipeline_logger()
        log_path = get_log_file_path()
        
        assert log_path is not None
        assert isinstance(log_path, Path)
        assert log_path.exists()
        assert log_path.suffix == ".log"
        assert log_path.parent.exists()

    def test_log_pipeline_start(self):
        """Test pipeline start logging."""
        log_pipeline_start(config={"test": "value"})
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "PIPELINE EXECUTION STARTED" in content
        assert "Configuration" in content
        assert "test" in content

    def test_log_pipeline_end(self):
        """Test pipeline end logging."""
        log_pipeline_end(status="SUCCESS")
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "PIPELINE EXECUTION ENDED: SUCCESS" in content

    def test_log_error(self):
        """Test error logging with traceback."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            log_error("TEST_TASK", e, {"key": "value"})
        
        log_path = get_log_file_path()
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "ERROR in task 'TEST_TASK'" in content
        assert "ValueError" in content
        assert "Traceback" in content
        assert "key" in content

    def test_log_metric(self):
        """Test metric logging."""
        log_metric("test_metric", 42, "units", task="TEST")
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "METRIC: test_metric = 42 [units]" in content
        assert "Task: TEST" in content

    def test_log_chunk_info(self):
        """Test chunk info logging."""
        log_chunk_info(1, 10, 100, 0.5)
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "CHUNK [1/10]" in content
        assert "Records: 100" in content
        assert "Elapsed: 0.50s" in content

    def test_log_task_start(self):
        """Test task start logging."""
        log_task_start("T001", "Setup task")
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "TASK START: T001" in content
        assert "Setup task" in content

    def test_log_task_end(self):
        """Test task end logging."""
        log_task_end("T001", status="COMPLETED", output_files=["data/test.csv"])
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "TASK END: T001 -> COMPLETED" in content
        assert "data/test.csv" in content

    def test_log_data_file_created(self):
        """Test data file creation logging."""
        log_data_file_created("data/processed/test.csv", 1.5, 1000)
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "DATA CREATED: data/processed/test.csv" in content
        assert "Size: 1.50 MB" in content
        assert "Records: 1000" in content

    def test_logger_reuse(self):
        """Test that logger instance is reused."""
        logger1 = get_pipeline_logger()
        logger2 = get_pipeline_logger()
        assert logger1 is logger2

    def test_log_format(self):
        """Test that log format includes required fields."""
        logger = get_pipeline_logger()
        logger.info("Test message")
        log_path = get_log_file_path()
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Find the test message line
        test_line = None
        for line in lines:
            if "Test message" in line:
                test_line = line
                break
        
        assert test_line is not None
        # Check for timestamp, level, and message
        assert "|" in test_line
        assert "INFO" in test_line
        assert "llmXive_pipeline" in test_line