"""
Unit tests for logging utilities.
"""
import pytest
import logging
from pathlib import Path
import tempfile
import os

# Mock config for testing
class MockConfig:
    LOG_DIR = Path(tempfile.gettempdir())
    LOG_LEVEL = logging.INFO

# Patch config before importing logger
import sys
sys.modules['config'] = MockConfig()

from utils.logger import setup_logger, get_logger, log_excluded_subjects, log_feature_filtering

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_setup_logger_creates_file(temp_log_dir):
    """Test that setup_logger creates a log file."""
    logger = setup_logger(
        name="test_logger",
        log_dir=temp_log_dir,
        level=logging.INFO
    )
    
    log_file = temp_log_dir / "test_logger.log"
    assert log_file.exists()
    assert isinstance(logger, logging.Logger)

def test_get_logger_returns_existing_instance(temp_log_dir):
    """Test that get_logger returns the same instance."""
    # Reset global state for test
    import utils.logger
    utils.logger._logger_instance = None
    
    logger1 = setup_logger(name="test_unique", log_dir=temp_log_dir)
    logger2 = get_logger()
    
    assert logger1 is logger2

def test_log_excluded_subjects_writes_file(temp_log_dir):
    """Test that excluded subjects are logged to file."""
    # Reset global state
    import utils.logger
    utils.logger._logger_instance = None
    
    # Create a custom config mock for this test
    class CustomConfig:
        LOG_DIR = temp_log_dir
        LOG_LEVEL = logging.INFO
        DATA_PROCESSED_DIR = temp_log_dir / "data" / "processed"
    
    sys.modules['config'] = CustomConfig()
    
    # Re-import to pick up new config
    import importlib
    importlib.reload(utils.logger)
    from utils.logger import log_excluded_subjects, get_logger
    
    subjects = ["sub-001", "sub-002"]
    reason = "Missing MMSE scores"
    
    log_excluded_subjects(subjects, reason, log_path=temp_log_dir / "excluded_test.log")
    
    log_file = temp_log_dir / "excluded_test.log"
    assert log_file.exists()
    
    content = log_file.read_text()
    assert "Missing MMSE scores" in content
    assert "sub-001" in content
    assert "sub-002" in content

def test_log_feature_filtering_logs_to_console(temp_log_dir):
    """Test that feature filtering logs to logger."""
    # Reset global state
    import utils.logger
    utils.logger._logger_instance = None
    
    class CustomConfig:
        LOG_DIR = temp_log_dir
        LOG_LEVEL = logging.INFO
        DATA_PROCESSED_DIR = temp_log_dir / "data" / "processed"
    
    sys.modules['config'] = CustomConfig()
    
    import importlib
    importlib.reload(utils.logger)
    from utils.logger import log_feature_filtering, get_logger
    
    features = ["feature_1", "feature_2"]
    reason = "High collinearity"
    
    # This should not raise an exception
    log_feature_filtering(features, reason)
    
    logger = get_logger()
    assert logger is not None