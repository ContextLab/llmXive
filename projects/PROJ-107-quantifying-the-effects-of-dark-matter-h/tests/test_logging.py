import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

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
from utils.config import get_project_root, get_logs_path

class TestLoggingInfrastructure:
    """Tests for the base logging infrastructure."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up a temporary logs directory for testing."""
        self.original_logs_path = get_logs_path()
        # Create a temporary directory for logs during tests
        self.temp_log_dir = Path(tempfile.mkdtemp())
        # Monkey patch get_logs_path to use temp directory
        import utils.config
        self.original_get_logs_path = utils.config.get_logs_path
        utils.config.get_logs_path = lambda: self.temp_log_dir
        return self

    def teardown(self):
        """Clean up the temporary logs directory."""
        import utils.config
        utils.config.get_logs_path = self.original_get_logs_path
        shutil.rmtree(self.temp_log_dir, ignore_errors=True)

    def test_get_pipeline_logger_creates_logger(self):
        """Test that get_pipeline_logger creates a logger with correct handlers."""
        logger = get_pipeline_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        assert len(logger.handlers) >= 2  # File and Console handlers
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_get_log_file_path_returns_valid_path(self):
        """Test that get_log_file_path returns a valid path for a logger with a file handler."""
        logger = get_pipeline_logger("test_file_path")
        path = get_log_file_path(logger)
        assert path is not None
        assert isinstance(path, Path)
        assert path.exists()

    def test_log_pipeline_start_logs_correct_info(self, caplog):
        """Test that log_pipeline_start logs the correct start information."""
        logger = get_pipeline_logger("test_start")
        with caplog.at_level(logging.INFO):
            log_pipeline_start(logger, "T006", "Setup")
        assert "PIPELINE START: Task T006, Stage: Setup" in caplog.text
        assert "Started at:" in caplog.text

    def test_log_pipeline_end_logs_correct_info(self, caplog):
        """Test that log_pipeline_end logs the correct end information."""
        logger = get_pipeline_logger("test_end")
        with caplog.at_level(logging.INFO):
            log_pipeline_end(logger, "T006", "SUCCESS", 12.5)
        assert "PIPELINE END: Task T006" in caplog.text
        assert "Status: SUCCESS" in caplog.text
        assert "Duration: 12.50 seconds" in caplog.text

    def test_log_error_logs_exception(self, caplog):
        """Test that log_error logs the exception and context."""
        logger = get_pipeline_logger("test_error")
        test_error = ValueError("Test error message")
        with caplog.at_level(logging.ERROR):
            log_error(logger, test_error, "Test context")
        assert "ERROR: Test error message" in caplog.text
        assert "Context: Test context" in caplog.text
        assert "ValueError" in caplog.text

    def test_log_metric_logs_value(self, caplog):
        """Test that log_metric logs the metric value and unit."""
        logger = get_pipeline_logger("test_metric")
        with caplog.at_level(logging.INFO):
            log_metric(logger, "accuracy", 0.95, "percent")
        assert "METRIC: accuracy (percent) = 0.95" in caplog.text

    def test_log_chunk_info_logs_chunk_details(self, caplog):
        """Test that log_chunk_info logs chunk processing details."""
        logger = get_pipeline_logger("test_chunk")
        with caplog.at_level(logging.INFO):
            log_chunk_info(logger, 1, 10, 500, 2.3)
        assert "CHUNK: 1/10" in caplog.text
        assert "Rows: 500" in caplog.text
        assert "Time: 2.30s" in caplog.text

    def test_log_task_start_logs_task_name(self, caplog):
        """Test that log_task_start logs the task name."""
        logger = get_pipeline_logger("test_task_start")
        with caplog.at_level(logging.INFO):
            log_task_start(logger, "T006_Implementation")
        assert "TASK START: T006_Implementation" in caplog.text

    def test_log_task_end_logs_status(self, caplog):
        """Test that log_task_end logs the task status."""
        logger = get_pipeline_logger("test_task_end")
        with caplog.at_level(logging.INFO):
            log_task_end(logger, "T006_Implementation", "SUCCESS")
        assert "TASK END: T006_Implementation" in caplog.text
        assert "Status: SUCCESS" in caplog.text

    def test_log_data_file_created_logs_file_info(self, caplog):
        """Test that log_data_file_created logs file creation details."""
        logger = get_pipeline_logger("test_data_file")
        test_path = self.temp_log_dir / "test_output.csv"
        with caplog.at_level(logging.INFO):
            log_data_file_created(logger, test_path, 100)
        assert "DATA FILE CREATED: test_output.csv" in caplog.text
        assert "Rows: 100" in caplog.text
        assert str(test_path) in caplog.text