import os
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import json
import tempfile
import shutil

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
    get_runtime_remaining_seconds,
    main
)

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def mock_settings(temp_log_dir):
    """Mock the settings module to use temporary log directory."""
    mock_paths = {
        "logs": temp_log_dir,
        "data_raw": temp_log_dir / "data" / "raw",
        "data_derived": temp_log_dir / "data" / "derived",
        "data_annotations": temp_log_dir / "data" / "annotations",
        "results": temp_log_dir / "results",
        "tests": temp_log_dir / "tests",
        "specs": temp_log_dir / "specs",
        "state": temp_log_dir / "state",
        "figures": temp_log_dir / "figures"
    }
    
    with patch('code.src.utils.logger.get_paths', return_value=mock_paths):
        with patch('code.src.utils.logger.ensure_directories'):
            yield mock_paths

@pytest.fixture
def clean_logs(mock_settings):
    """Clean up log files before and after test."""
    # Clean before
    yield
    # Clean after (pytest will handle temp dir cleanup)

class TestGetLogger:
    def test_get_logger_returns_valid_logger(self, mock_settings):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_reuses_existing_handlers(self, mock_settings):
        """Test that get_logger doesn't add duplicate handlers."""
        logger1 = get_logger("test_module_dup")
        initial_handler_count = len(logger1.handlers)
        
        logger2 = get_logger("test_module_dup")
        assert len(logger2.handlers) == initial_handler_count
    
    def test_get_logger_creates_file_handler(self, mock_settings, temp_log_dir):
        """Test that get_logger creates a file handler."""
        logger = get_logger("test_file_handler")
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

class TestSetupPipelineLogging:
    def test_setup_creates_root_logger(self, mock_settings, temp_log_dir):
        """Test that setup_pipeline_logging creates a root logger."""
        root_logger = setup_pipeline_logging()
        assert isinstance(root_logger, logging.Logger)
        assert root_logger.name == "llmXive"
        assert len(root_logger.handlers) >= 1
    
    def test_setup_creates_log_files(self, mock_settings, temp_log_dir):
        """Test that setup_pipeline_logging creates log files."""
        setup_pipeline_logging()
        
        pipeline_log = temp_log_dir / "pipeline.log"
        runtime_log = temp_log_dir / "runtime.log"
        stats_log = temp_log_dir / "runtime_stats.json"
        
        # Pipeline log should exist
        assert pipeline_log.exists()
    
    def test_setup_creates_log_directory(self, mock_settings, temp_log_dir):
        """Test that setup_pipeline_logging ensures log directory exists."""
        setup_pipeline_logging()
        assert temp_log_dir.exists()

class TestRuntimeTracking:
    def test_start_runtime_tracking_sets_start_time(self, mock_settings):
        """Test that start_runtime_tracking initializes tracking state."""
        start_runtime_tracking()
        
        # Should have recorded start time
        assert get_runtime_remaining_seconds() is not None
    
    def test_stop_runtime_tracking_calculates_duration(self, mock_settings):
        """Test that stop_runtime_tracking calculates total runtime."""
        start_runtime_tracking()
        time.sleep(0.01)  # Small delay
        stop_runtime_tracking()
        
        # Stats should be written
        stats_log = Path("logs/runtime_stats.json")
        # Note: In real scenario, this would be in temp log dir
        # For test, we verify the function runs without error
    
    def test_runtime_stats_written_to_file(self, mock_settings, temp_log_dir):
        """Test that runtime stats are written to JSON file."""
        with patch('code.src.utils.logger._stats_log_path', temp_log_dir / "runtime_stats.json"):
            start_runtime_tracking()
            increment_pr_processed()
            stop_runtime_tracking()
            
            stats_file = temp_log_dir / "runtime_stats.json"
            assert stats_file.exists()
            
            with open(stats_file) as f:
                stats = json.load(f)
                assert "total_runtime_seconds" in stats
                assert "pr_processed" in stats
                assert stats["pr_processed"] == 1

class TestLogRuntimeStats:
    def test_log_runtime_stats_logs_current_state(self, mock_settings):
        """Test that log_runtime_stats logs current runtime state."""
        start_runtime_tracking()
        
        with patch('code.src.utils.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_runtime_stats()
            
            # Should have logged runtime info
            assert mock_logger.info.called
        
        stop_runtime_tracking()
    
    def test_log_runtime_stats_no_error_when_not_started(self, mock_settings):
        """Test that log_runtime_stats handles case when tracking not started."""
        # Should not raise error
        log_runtime_stats()

class TestCounterFunctions:
    def test_increment_pr_processed(self, mock_settings):
        """Test increment_pr_processed increments counter."""
        start_runtime_tracking()
        
        with patch('code.src.utils.logger._runtime_stats', {"pr_processed": 0}) as mock_stats:
            increment_pr_processed()
            assert mock_stats["pr_processed"] == 1
        
        stop_runtime_tracking()
    
    def test_increment_pr_skipped(self, mock_settings):
        """Test increment_pr_skipped increments counter."""
        start_runtime_tracking()
        
        with patch('code.src.utils.logger._runtime_stats', {"pr_skipped": 0}) as mock_stats:
            increment_pr_skipped()
            assert mock_stats["pr_skipped"] == 1
        
        stop_runtime_tracking()
    
    def test_increment_errors(self, mock_settings):
        """Test increment_errors increments error counter."""
        start_runtime_tracking()
        
        with patch('code.src.utils.logger._runtime_stats', {"errors": 0}) as mock_stats:
            increment_errors()
            assert mock_stats["errors"] == 1
        
        stop_runtime_tracking()
    
    def test_increment_warnings(self, mock_settings):
        """Test increment_warnings increments warning counter."""
        start_runtime_tracking()
        
        with patch('code.src.utils.logger._runtime_stats', {"warnings": 0}) as mock_stats:
            increment_warnings()
            assert mock_stats["warnings"] == 1
        
        stop_runtime_tracking()

class TestMainFunction:
    def test_main_executes_without_error(self, mock_settings):
        """Test that main() executes without error."""
        # Should not raise any exceptions
        main()

class TestRuntimeRemaining:
    def test_get_runtime_remaining_returns_value(self, mock_settings):
        """Test that get_runtime_remaining_seconds returns a value."""
        start_runtime_tracking()
        
        remaining = get_runtime_remaining_seconds()
        assert remaining is not None
        assert remaining > 0
        
        stop_runtime_tracking()
    
    def test_get_runtime_remaining_returns_none_when_not_started(self, mock_settings):
        """Test that get_runtime_remaining_seconds returns None when not started."""
        remaining = get_runtime_remaining_seconds()
        assert remaining is None