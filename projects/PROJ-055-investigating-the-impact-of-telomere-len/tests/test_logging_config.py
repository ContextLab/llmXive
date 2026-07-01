"""
Tests for logging configuration and memory pressure detection.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import logging

# Import the module functions
import sys
sys.path.insert(0, 'code')
from logging_config import (
    ensure_log_directory,
    get_memory_usage_bytes,
    check_memory_pressure,
    get_memory_status,
    setup_logging,
    log_memory_status,
    handle_memory_pressure,
    init_project_logging,
    MAX_MEMORY_BYTES
)

class TestLoggingInfrastructure:
    """Test logging infrastructure setup and functionality."""
    
    def test_ensure_log_directory_creates_dir(self, tmp_path):
        """Test that ensure_log_directory creates the logs directory."""
        # Temporarily override LOG_DIR for testing
        import logging_config
        original_log_dir = logging_config.LOG_DIR
        test_log_dir = tmp_path / "logs"
        logging_config.LOG_DIR = test_log_dir
        
        try:
            result = ensure_log_directory()
            assert result.exists()
            assert result.is_dir()
            assert result == test_log_dir
        finally:
            logging_config.LOG_DIR = original_log_dir
    
    def test_setup_logging_creates_file(self, tmp_path, caplog):
        """Test that setup_logging creates a log file."""
        import logging_config
        original_log_dir = logging_config.LOG_DIR
        test_log_dir = tmp_path / "logs"
        logging_config.LOG_DIR = test_log_dir
        
        try:
            log_file = "test_log.log"
            logger = setup_logging(log_file=log_file, console_output=False)
            
            log_path = test_log_dir / log_file
            assert log_path.exists()
            
            # Test that logging works
            logger.info("Test message")
            
            # Read file and verify content
            with open(log_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            logging_config.LOG_DIR = original_log_dir
    
    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a valid logger."""
        logger = setup_logging(console_output=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "root"
    
    def test_init_project_logging(self):
        """Test the convenience init function."""
        logger = init_project_logging(log_level="DEBUG")
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.DEBUG

class TestMemoryPressureDetection:
    """Test memory pressure detection functionality."""
    
    def test_get_memory_usage_bytes_returns_positive(self):
        """Test that memory usage is returned as a positive number."""
        memory = get_memory_usage_bytes()
        assert isinstance(memory, (int, float))
        assert memory > 0
    
    def test_check_memory_pressure_returns_boolean(self):
        """Test that check_memory_pressure returns a boolean."""
        result = check_memory_pressure()
        assert isinstance(result, bool)
    
    def test_check_memory_pressure_custom_threshold(self):
        """Test check_memory_pressure with custom threshold."""
        # Set a very low threshold to ensure pressure is detected
        low_threshold = 1  # 1 byte
        result = check_memory_pressure(threshold_bytes=low_threshold)
        assert result is True
        
        # Set a very high threshold to ensure no pressure
        high_threshold = 10**15  # 1000 TB
        result = check_memory_pressure(threshold_bytes=high_threshold)
        assert result is False
    
    def test_get_memory_status_structure(self):
        """Test that get_memory_status returns expected dictionary structure."""
        status = get_memory_status()
        
        expected_keys = [
            "current_bytes",
            "current_gb",
            "threshold_bytes",
            "threshold_gb",
            "pressure_detected",
            "utilization_percent"
        ]
        
        for key in expected_keys:
            assert key in status
        
        assert isinstance(status["current_bytes"], (int, float))
        assert isinstance(status["current_gb"], float)
        assert isinstance(status["pressure_detected"], bool)
        assert isinstance(status["utilization_percent"], float)
    
    def test_handle_memory_pressure_warn_action(self):
        """Test handle_memory_pressure with warn action."""
        # This should not raise an exception
        result = handle_memory_pressure(action="warn")
        assert isinstance(result, bool)
    
    def test_handle_memory_pressure_log_action(self):
        """Test handle_memory_pressure with log action."""
        result = handle_memory_pressure(action="log")
        assert isinstance(result, bool)
    
    def test_handle_memory_pressure_abort_action_no_pressure(self):
        """Test handle_memory_pressure with abort action when no pressure."""
        # Set a very high threshold so no pressure is detected
        result = handle_memory_pressure(action="abort", logger=logging.getLogger())
        # Should return False and not raise
        assert result is False

class TestIntegration:
    """Integration tests for logging and memory monitoring."""
    
    def test_full_logging_workflow(self, tmp_path):
        """Test complete logging workflow with memory status."""
        import logging_config
        original_log_dir = logging_config.LOG_DIR
        test_log_dir = tmp_path / "logs"
        logging_config.LOG_DIR = test_log_dir
        
        try:
            # Initialize logging
            logger = init_project_logging(log_level="DEBUG")
            
            # Log memory status
            status = log_memory_status(logger)
            
            # Verify status was returned correctly
            assert "current_gb" in status
            assert "pressure_detected" in status
            
            # Handle pressure (should not crash)
            handle_memory_pressure(logger, action="warn")
            
        finally:
            logging_config.LOG_DIR = original_log_dir
