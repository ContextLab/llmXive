import pytest
import logging
import sys
from io import StringIO
from code.utils import log_setup

def test_log_setup_format():
    """Test that log_setup produces the correct format."""
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        logger = log_setup(level=logging.INFO, destination='stdout')
        logger.info("Test message")
        
        output = captured_output.getvalue()
        
        # Check format: [%(asctime)s] %(levelname)s: %(message)s
        # The exact timestamp will vary, but structure must match
        assert "[INFO]" in output or "INFO" in output
        assert "Test message" in output
        assert output.startswith("[")
        assert "]" in output
    finally:
        sys.stdout = old_stdout

def test_log_setup_level():
    """Test that log_setup respects the logging level."""
    logger = log_setup(level=logging.WARNING, destination='stdout')
    
    # This should not appear if level is WARNING
    # We can't easily capture this without redirecting, 
    # but we can verify the logger's level
    assert logger.level == logging.WARNING

def test_log_setup_destination_file():
    """Test that log_setup can write to a file."""
    import os
    from pathlib import Path
    
    logger = log_setup(level=logging.INFO, destination='file')
    logger.info("File test message")
    
    # Verify log file exists
    log_path = Path("logs/app.log")
    assert log_path.exists()
    
    # Clean up
    log_path.unlink()
    if not list(Path("logs").glob("*")):
        Path("logs").rmdir()
