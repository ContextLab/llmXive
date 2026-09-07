"""
Tests for the logger module.
"""
import os
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.utils.logger import (
    get_logger,
    setup_pipeline_logging,
    start_runtime_tracking,
    stop_runtime_tracking,
    log_runtime_stats,
    main
)
from code.config.settings import get_paths


@pytest.fixture
def clean_logs():
    """Clean up log files before and after tests."""
    paths = get_paths()
    log_dir = Path(paths["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Store existing log files
    existing_files = list(log_dir.glob("*.log"))
    
    yield log_dir
    
    # Clean up log files created during test
    for log_file in log_dir.glob("*.log"):
        if log_file not in existing_files:
            log_file.unlink()


class TestGetLogger:
    def test_get_logger_creates_logger(self):
        """Test that get_logger creates and returns a logger."""
        logger = get_logger("test_get_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_get_logger"
    
    def test_get_logger_returns_same_instance(self):
        """Test that calling get_logger twice returns the same configured logger."""
        logger1 = get_logger("test_same_instance")
        logger2 = get_logger("test_same_instance")
        assert logger1 is logger2
    
    def test_get_logger_has_handlers(self):
        """Test that logger has both file and console handlers."""
        logger = get_logger("test_handlers")
        assert len(logger.handlers) >= 2  # File and console handlers


class TestRuntimeTracking:
    def test_start_runtime_tracking(self, clean_logs):
        """Test that start_runtime_tracking initializes tracking."""
        start_info = start_runtime_tracking()
        
        assert "start_time" in start_info
        assert "start_datetime" in start_info
        assert start_info["status"] == "started"
        assert isinstance(start_info["start_time"], float)
    
    def test_stop_runtime_tracking_requires_start(self, clean_logs):
        """Test that stop_runtime_tracking fails if not started."""
        # Reset global state by importing fresh module
        import importlib
        import code.src.utils.logger as logger_module
        importlib.reload(logger_module)
        
        with pytest.raises(RuntimeError, match="Runtime tracking was not started"):
            logger_module.stop_runtime_tracking()
    
    def test_start_and_stop_runtime_tracking(self, clean_logs):
        """Test that start and stop tracking work together."""
        start_info = start_runtime_tracking()
        time.sleep(0.1)
        end_info = stop_runtime_tracking()
        
        assert "end_time" in end_info
        assert "duration_seconds" in end_info
        assert end_info["status"] == "completed"
        assert end_info["duration_seconds"] >= 0.1


class TestSetupPipelineLogging:
    def test_setup_pipeline_logging_creates_logger(self, clean_logs):
        """Test that setup_pipeline_logging returns a logger."""
        logger = setup_pipeline_logging("INFO")
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO
    
    def test_setup_pipeline_logging_creates_log_dir(self, clean_logs):
        """Test that setup_pipeline_logging creates the log directory."""
        setup_pipeline_logging("INFO")
        
        paths = get_paths()
        log_dir = Path(paths["logs"])
        assert log_dir.exists()
    
    def test_setup_pipeline_logging_creates_log_file(self, clean_logs):
        """Test that setup_pipeline_logging creates the pipeline log file."""
        setup_pipeline_logging("INFO")
        
        paths = get_paths()
        log_dir = Path(paths["logs"])
        pipeline_log = log_dir / "pipeline.log"
        assert pipeline_log.exists()


class TestLogRuntimeStats:
    def test_log_runtime_stats(self, clean_logs):
        """Test that log_runtime_stats logs statistics."""
        start_runtime_tracking()
        
        stats = {
            "test_key": "test_value",
            "number": 42
        }
        
        # This should not raise
        log_runtime_stats(stats)
        
        stop_runtime_tracking()


class TestMainFunction:
    def test_main_runs_without_error(self, clean_logs):
        """Test that main() runs without raising exceptions."""
        # This should complete successfully
        main()
        
        # Verify log files were created
        paths = get_paths()
        log_dir = Path(paths["logs"])
        assert (log_dir / "pipeline.log").exists()
        assert (log_dir / "runtime.log").exists()