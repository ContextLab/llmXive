import os
import tempfile
import shutil
import logging
import pytest
from code.utils.logging_setup import setup_logging, get_experiment_logger

def test_setup_logging_creates_file():
    """Test that setup_logging creates a log file in the specified directory."""
    temp_dir = tempfile.mkdtemp()
    log_dir = os.path.join(temp_dir, "logs")
    
    try:
        # Setup logging to temp directory
        setup_logging(log_level=logging.INFO, log_dir=log_dir, log_file_prefix="test")
        
        # Verify log directory exists
        assert os.path.isdir(log_dir), "Log directory was not created"
        
        # Verify a log file was created
        files = os.listdir(log_dir)
        assert len(files) > 0, "No log files created"
        
        # Verify it's a .log file
        log_files = [f for f in files if f.endswith('.log')]
        assert len(log_files) > 0, "No .log files found"
        
        # Log something and verify it's in the file
        logger = logging.getLogger()
        logger.info("Test message for verification")
        
        # Read the last log file
        latest_log = os.path.join(log_dir, log_files[-1])
        with open(latest_log, 'r') as f:
            content = f.read()
            assert "Test message for verification" in content, "Message not found in log file"
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        # Reset logging to avoid affecting other tests
        logging.getLogger().handlers.clear()

def test_get_experiment_logger():
    """Test that get_experiment_logger returns a valid logger."""
    temp_dir = tempfile.mkdtemp()
    log_dir = os.path.join(temp_dir, "logs")
    
    try:
        setup_logging(log_dir=log_dir)
        
        # Test with name
        logger = get_experiment_logger("TestComponent")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "TestComponent"
        
        # Test without name (root logger)
        root_logger = get_experiment_logger()
        assert root_logger is logging.getLogger()
        
    finally:
        shutil.rmtree(temp_dir)
        logging.getLogger().handlers.clear()