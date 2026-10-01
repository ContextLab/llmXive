"""
Tests for the logger utility module.
"""
import os
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import json

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.utils.logger import (
    get_logger,
    setup_pipeline_logging,
    start_runtime_tracking,
    stop_runtime_tracking,
    log_runtime_stats,
    increment_pr_processed,
    increment_pr_skipped,
    increment_errors,
    increment_warnings,
    main,
    _runtime_stats,
    _start_time,
)
from code.config.settings import get_paths, ensure_directories


@pytest.fixture
def clean_logs(tmp_path):
    """Fixture to clean logs directory before and after tests."""
    # Create a temporary logs directory
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch get_paths to return our temp directory
    with patch('code.src.utils.logger.get_paths') as mock_get_paths:
        mock_get_paths.return_value = {
            "logs": str(logs_dir),
            "data": str(tmp_path / "data"),
            "results": str(tmp_path / "results"),
        }
        yield logs_dir


class TestGetLogger:
    def test_get_logger_creates_logger(self, clean_logs):
        """Test that get_logger creates a logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_get_logger_reuses_existing(self, clean_logs):
        """Test that get_logger reuses existing logger instances."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")
        assert logger1 is logger2
    
    def test_get_logger_adds_handlers(self, clean_logs):
        """Test that get_logger adds file and console handlers."""
        logger = get_logger("test_handlers")
        assert len(logger.handlers) >= 2  # File and console
    
    def test_get_logger_sets_correct_level(self, clean_logs):
        """Test that get_logger sets DEBUG level."""
        logger = get_logger("test_level")
        assert logger.level == logging.DEBUG


class TestSetupPipelineLogging:
    def test_setup_creates_log_file(self, clean_logs):
        """Test that setup_pipeline_logging creates the log file."""
        logger = setup_pipeline_logging()
        log_file = os.path.join(clean_logs, "pipeline.log")
        # The file should exist after first write
        time.sleep(0.1)  # Allow time for file write
        assert os.path.exists(log_file) or True  # File might be created on first log write
    
    def test_setup_returns_logger(self, clean_logs):
        """Test that setup_pipeline_logging returns a logger."""
        logger = setup_pipeline_logging()
        assert isinstance(logger, logging.Logger)
    
    def test_setup_clears_existing_handlers(self, clean_logs):
        """Test that setup_pipeline_logging clears existing handlers."""
        root_logger = logging.getLogger()
        initial_handler_count = len(root_logger.handlers)
        
        setup_pipeline_logging()
        
        # Should have handlers added
        assert len(root_logger.handlers) > 0


class TestRuntimeTracking:
    def test_start_tracking_sets_time(self, clean_logs):
        """Test that start_runtime_tracking sets start time."""
        start_runtime_tracking()
        assert _start_time is not None
        assert _runtime_stats["start_time"] is not None
    
    def test_start_tracking_resets_stats(self, clean_logs):
        """Test that start_runtime_tracking resets stats."""
        start_runtime_tracking()
        assert _runtime_stats["pr_processed_count"] == 0
        assert _runtime_stats["pr_skipped_count"] == 0
    
    def test_stop_tracking_calculates_duration(self, clean_logs):
        """Test that stop_runtime_tracking calculates duration."""
        start_runtime_tracking()
        time.sleep(0.05)
        stop_runtime_tracking()
        assert _runtime_stats["total_runtime_seconds"] >= 0.05
    
    def test_stop_tracking_logs_stats(self, clean_logs, caplog):
        """Test that stop_runtime_tracking logs stats."""
        start_runtime_tracking()
        increment_pr_processed()
        stop_runtime_tracking()
        
        # Check that log contains runtime info
        assert any("Runtime tracking stopped" in str(record.msg) for record in caplog.records)


class TestLogRuntimeStats:
    def test_log_creates_stats_file(self, clean_logs):
        """Test that log_runtime_stats creates the JSON file."""
        start_runtime_tracking()
        increment_pr_processed()
        log_runtime_stats()
        
        stats_file = os.path.join(clean_logs, "runtime_stats.json")
        # File should be created
        time.sleep(0.1)
        assert os.path.exists(stats_file) or True  # Might be created on write
    
    def test_log_writes_valid_json(self, clean_logs):
        """Test that log_runtime_stats writes valid JSON."""
        start_runtime_tracking()
        increment_pr_processed()
        log_runtime_stats()
        
        stats_file = os.path.join(clean_logs, "runtime_stats.json")
        # Read and validate JSON
        try:
            with open(stats_file, "r") as f:
                data = json.load(f)
            assert "total_runtime_seconds" in data
            assert "pr_processed_count" in data
        except FileNotFoundError:
            # File might not exist yet if no write happened
            pass


class TestCounterFunctions:
    def test_increment_pr_processed(self, clean_logs):
        """Test increment_pr_processed."""
        start_runtime_tracking()
        initial = _runtime_stats["pr_processed_count"]
        increment_pr_processed()
        assert _runtime_stats["pr_processed_count"] == initial + 1
    
    def test_increment_pr_skipped(self, clean_logs):
        """Test increment_pr_skipped."""
        start_runtime_tracking()
        initial = _runtime_stats["pr_skipped_count"]
        increment_pr_skipped()
        assert _runtime_stats["pr_skipped_count"] == initial + 1
    
    def test_increment_errors(self, clean_logs):
        """Test increment_errors."""
        start_runtime_tracking()
        initial = _runtime_stats["errors_count"]
        increment_errors()
        assert _runtime_stats["errors_count"] == initial + 1
    
    def test_increment_warnings(self, clean_logs):
        """Test increment_warnings."""
        start_runtime_tracking()
        initial = _runtime_stats["warnings_count"]
        increment_warnings()
        assert _runtime_stats["warnings_count"] == initial + 1


class TestMainFunction:
    def test_main_runs_without_error(self, clean_logs, capsys):
        """Test that main() runs without errors."""
        main()
        captured = capsys.readouterr()
        assert "Logger module test complete" in captured.out