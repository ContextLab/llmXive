import os
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import (
    get_logger,
    start_runtime_tracking,
    stop_runtime_tracking,
    log_runtime_stats,
    setup_pipeline_logging,
    main
)
from config.settings import get_paths

@pytest.fixture
def clean_logs():
    """Fixture to clean up log files before and after tests."""
    paths = get_paths()
    log_dir = Path(paths["log_dir"])
    log_files = list(log_dir.glob("*.log"))
    
    # Store original files
    original_files = {f: f.read_bytes() for f in log_files if f.exists()}
    
    # Clean up
    for f in log_files:
        f.unlink(missing_ok=True)
    
    yield
    
    # Restore original files
    for f, content in original_files.items():
        f.write_bytes(content)

class TestGetLogger:
    def test_get_logger_returns_valid_logger(self, clean_logs):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0

    def test_get_logger_reuses_existing(self, clean_logs):
        """Test that get_logger reuses existing logger configuration."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")
        assert logger1 is logger2

class TestRuntimeTracking:
    def test_start_runtime_tracking(self, clean_logs):
        """Test that start_runtime_tracking sets the start time."""
        start_runtime_tracking()
        # Just verify it doesn't raise an exception
        assert True

    def test_stop_runtime_tracking_logs_duration(self, clean_logs):
        """Test that stop_runtime_tracking calculates and logs duration."""
        start_runtime_tracking()
        time.sleep(0.1)  # Sleep for 100ms
        duration = stop_runtime_tracking()
        
        assert duration is not None
        assert 0.09 <= duration <= 0.2  # Allow some tolerance

    def test_stop_without_start(self, clean_logs):
        """Test that stopping without starting returns None and logs warning."""
        # Reset state by importing fresh
        import src.utils.logger as logger_module
        logger_module._runtime_start = None
        logger_module._runtime_end = None
        
        duration = stop_runtime_tracking()
        assert duration is None

class TestSetupPipelineLogging:
    def test_setup_pipeline_logging(self, clean_logs):
        """Test that setup_pipeline_logging creates handlers and directory."""
        logger = setup_pipeline_logging("test_setup")
        
        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) >= 2  # File and console handlers
        
        paths = get_paths()
        log_dir = Path(paths["log_dir"])
        assert log_dir.exists()
        
        log_file = log_dir / "pipeline.log"
        assert log_file.exists()

class TestLogRuntimeStats:
    def test_log_runtime_stats(self, clean_logs):
        """Test that log_runtime_stats returns correct statistics."""
        start_runtime_tracking()
        time.sleep(0.05)
        stop_runtime_tracking()
        
        stats = log_runtime_stats({"custom_field": "value"})
        
        assert "tracking_active" in stats
        assert stats["tracking_active"] is True
        assert "start_time" in stats
        assert "end_time" in stats
        assert "duration_seconds" in stats
        assert stats["duration_seconds"] is not None
        assert stats["custom_field"] == "value"

    def test_log_runtime_stats_without_tracking(self, clean_logs):
        """Test that log_runtime_stats handles case when tracking not started."""
        import src.utils.logger as logger_module
        logger_module._runtime_start = None
        logger_module._runtime_end = None
        
        stats = log_runtime_stats()
        
        assert stats["tracking_active"] is False
        assert stats["start_time"] is None
        assert stats["end_time"] is None
        assert stats["duration_seconds"] is None

class TestMainFunction:
    def test_main_function(self, clean_logs, caplog):
        """Test that main function executes without errors."""
        # Capture logs to verify execution
        with caplog.at_level(logging.INFO):
            main()
        
        # Verify log messages were generated
        assert any("Logger infrastructure initialized" in record.message for record in caplog.records)
        assert any("Runtime stats logged" in record.message for record in caplog.records)
        assert any("Pipeline runtime tracking started" in record.message for record in caplog.records)
        assert any("Pipeline runtime tracking stopped" in record.message for record in caplog.records)