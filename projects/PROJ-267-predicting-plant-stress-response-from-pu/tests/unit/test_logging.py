"""
Unit tests for the logging infrastructure.

Tests verify that:
1. Logging is properly configured
2. Warnings are captured to logs/pipeline.log
3. Log messages contain expected content
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import setup_logging, get_logger, log_warning
from utils.config import get_log_path


class TestLoggingConfig:
    """Tests for logging configuration and setup."""
    
    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that setup_logging creates file and console handlers."""
        # Temporarily override config paths
        import utils.logging_config
        original_path = utils.logging_config.LOG_PATH
        test_log_path = str(tmp_path / "test_pipeline.log")
        utils.logging_config.LOG_PATH = test_log_path
        
        try:
            logger = setup_logging()
            
            # Check handlers exist
            assert len(logger.handlers) >= 2, "Should have at least file and console handlers"
            
            # Check file handler exists
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0, "Should have a file handler"
            
            # Check log file is created
            assert Path(test_log_path).exists(), "Log file should be created"
            
        finally:
            # Restore original path
            utils.logging_config.LOG_PATH = original_path
    
    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns a properly named logger."""
        test_name = "test_module_name"
        logger = get_logger(test_name)
        
        assert logger.name == test_name, f"Logger name should be {test_name}"
        assert isinstance(logger, logging.Logger), "Should return a Logger instance"
    
    def test_get_logger_auto_detects_caller(self):
        """Test that get_logger auto-detects caller module name when not provided."""
        logger = get_logger()
        
        assert isinstance(logger, logging.Logger), "Should return a Logger instance"
        assert len(logger.name) > 0, "Logger should have a name"
    
    def test_log_warning_logs_to_file(self, tmp_path):
        """Test that log_warning writes to the log file."""
        import utils.logging_config
        original_path = utils.logging_config.LOG_PATH
        test_log_path = str(tmp_path / "test_warning.log")
        utils.logging_config.LOG_PATH = test_log_path
        
        try:
            setup_logging()
            
            # Log a warning
            test_message = "Test warning message for verification"
            log_warning(test_message, "test_warning_module")
            
            # Verify message is in file
            with open(test_log_path, 'r') as f:
                content = f.read()
                
            assert test_message in content, f"Warning message should be in log file"
            
        finally:
            utils.logging_config.LOG_PATH = original_path
    
    def test_log_warning_with_default_logger(self, tmp_path):
        """Test log_warning with auto-detected logger name."""
        import utils.logging_config
        original_path = utils.logging_config.LOG_PATH
        test_log_path = str(tmp_path / "test_default.log")
        utils.logging_config.LOG_PATH = test_log_path
        
        try:
            setup_logging()
            
            # Log a warning without specifying logger name
            test_message = "Test warning with default logger"
            log_warning(test_message)
            
            # Verify message is in file
            with open(test_log_path, 'r') as f:
                content = f.read()
                
            assert test_message in content, f"Warning message should be in log file"
            
        finally:
            utils.logging_config.LOG_PATH = original_path


class TestLoggingIntegration:
    """Integration tests for logging in the pipeline context."""
    
    def test_logging_pipeline_log_exists(self):
        """Test that the pipeline log file path is valid and writable."""
        log_path = get_log_path()
        log_dir = Path(log_path).parent
        
        # Directory should exist or be creatable
        assert log_dir.exists() or log_dir.parent.exists(), "Log directory should exist"
        
        # Should be able to create the log file
        test_file = log_dir / "test_write.log"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Cannot write to log directory: {e}")
    
    def test_logging_capture_warnings(self, tmp_path):
        """Test that various warning types are captured correctly."""
        import utils.logging_config
        original_path = utils.logging_config.LOG_PATH
        test_log_path = str(tmp_path / "test_warnings.log")
        utils.logging_config.LOG_PATH = test_log_path
        
        try:
            setup_logging()
            logger = get_logger("test_warnings")
            
            # Log different types of warnings
            warnings_to_log = [
                "Dropped 10 rows due to missing values",
                "Missing data in column 'protein_abundance'",
                "Sample 'Sample_001' excluded due to insufficient data",
                "Warning: Low detection rate for protein 'P12345'"
            ]
            
            for warning in warnings_to_log:
                log_warning(warning, "test_warnings")
            
            # Verify all warnings are in the log file
            with open(test_log_path, 'r') as f:
                content = f.read()
            
            for warning in warnings_to_log:
                assert warning in content, f"Warning '{warning}' should be in log file"
            
        finally:
            utils.logging_config.LOG_PATH = original_path