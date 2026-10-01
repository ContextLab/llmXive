import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging_config import setup_logging, get_logger, log_warning
from utils.config import LOG_PATH

def test_logging_setup():
    """Test that logging infrastructure is correctly configured."""
    # Ensure the log directory exists
    log_dir = Path(LOG_PATH).parent
    assert log_dir.exists(), f"Log directory {log_dir} does not exist"

    # Setup logging
    logger = setup_logging()
    assert logger is not None
    assert logger.level == logging.INFO or logger.level == logging.WARNING

    # Test logger retrieval
    sub_logger = get_logger("test_submodule")
    assert sub_logger is not None
    assert sub_logger.name == "test_submodule"

    # Test log file creation
    log_warning("Test warning message for T006 verification")
    
    # Check if log file exists and contains the message
    # Note: In some environments, file flushing might be delayed, but RotatingFileHandler usually flushes on write.
    assert LOG_PATH.exists(), f"Log file {LOG_PATH} was not created"
    
    with open(LOG_PATH, 'r') as f:
        content = f.read()
        assert "Test warning message for T006 verification" in content, "Warning message not found in log file"
        assert "WARNING" in content, "Log level not recorded correctly"

    print("Logging infrastructure test passed.")

if __name__ == "__main__":
    test_logging_setup()