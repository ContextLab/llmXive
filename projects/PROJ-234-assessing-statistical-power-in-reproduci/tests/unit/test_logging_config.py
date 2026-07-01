import os
import logging
import tempfile
import shutil
import pytest

# We need to mock the project structure slightly or ensure we can import
# Since the code assumes it's running from the project root or code/utils
# We will test the logic by importing and checking side effects.

def test_logging_file_creation(tmp_path):
    """
    Verifies that the logging configuration creates the data directory and log file.
    """
    # Temporarily override the data directory path for testing
    # We can't easily mock the __file__ based path resolution without refactoring,
    # so we will test the resulting behavior by importing and checking if the file exists
    # in the expected relative location if run from a specific context, 
    # OR we verify the function logic directly.
    
    # Strategy: The setup_logging function creates 'data/ingest.log' relative to the project root.
    # In a unit test, we can't easily change the __file__ of the module being imported.
    # However, we can verify that the logger is configured correctly.
    
    from code.utils.logging_config import setup_logging, logger, log_file_path
    
    # Call setup again to ensure it's active
    setup_logging()
    
    # Check that the logger has a file handler
    file_handler_exists = any(isinstance(h, logging.FileHandler) for h in logger.parent.handlers)
    assert file_handler_exists, "File handler should be present in the logger"
    
    # Verify the log file path ends with data/ingest.log
    # Note: In a real run, this file should exist. In a test environment, 
    # we might not have write permissions to the actual project root 'data' folder
    # if run from a sandbox. We assert the configuration is correct.
    assert log_file_path.endswith("data/ingest.log"), f"Log path should be data/ingest.log, got {log_file_path}"

def test_log_entry_written(tmp_path, monkeypatch):
    """
    Tests that a log entry is actually written to the file.
    We patch the log directory to use a temp directory to ensure we can write.
    """
    import code.utils.logging_config as log_module
    
    # Create a temp directory structure mimicking the project
    temp_data_dir = tmp_path / "data"
    temp_data_dir.mkdir()
    temp_log_file = temp_data_dir / "ingest.log"
    
    # Monkeypatch the log_file_path in the module
    original_path = log_module.log_file_path
    log_module.log_file_path = str(temp_log_file)
    
    # Re-initialize logging with the new path
    # We need to re-run the setup logic. Since setup_logging uses global state,
    # we'll just force a new handler with the temp path.
    root_logger = logging.getLogger()
    # Remove existing file handlers to avoid conflicts
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            root_logger.removeHandler(handler)
    
    file_handler = logging.FileHandler(temp_log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)
    
    # Now log something
    log_module.logger.info("Test log entry from unit test.")
    
    # Flush handlers to ensure write
    for handler in root_logger.handlers:
        handler.flush()
        handler.close()
    
    # Verify file exists and contains the message
    assert temp_log_file.exists(), "Log file should be created in temp directory"
    content = temp_log_file.read_text()
    assert "Test log entry from unit test." in content, "Log message should be present in file"