import os
import sys
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from src.utils.resource_monitor import check_wall_time_limit, get_elapsed_seconds
from src.utils.logging_config import setup_logging, get_logger

def setup_module():
    """Setup logging for the test module."""
    setup_logging(level="INFO", format_type="json")

@pytest.mark.contract
def test_timeout_handler_logging():
    """
    Contract test: Verify that the timeout handler logs "TIMEOUT_WARNING"
    when the wall-time limit is reached, without crashing the process.
    
    This verifies the requirement in T015: 
    'enforce a 6-hour (21600s) wall-time limit ... Log "TIMEOUT_WARNING" but DO NOT abort.'
    """
    logger = get_logger(__name__)
    
    # Set a very short timeout for testing (2 seconds)
    test_timeout_seconds = 2.0
    
    # Mock the start time to simulate time passing
    start_time = time.time() - (test_timeout_seconds + 10) # Pretend we started 10s ago
    
    # Capture logs to verify the warning message
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)
    
    # Check wall time limit
    # The function check_wall_time_limit returns True if within limit, False if exceeded
    # It is expected to log the warning internally if exceeded
    is_within_limit = check_wall_time_limit(start_time, test_timeout_seconds)
    
    # Get the log output
    log_output = log_stream.getvalue()
    
    # Verify the warning was logged
    assert "TIMEOUT_WARNING" in log_output, (
        f"Expected 'TIMEOUT_WARNING' in logs, but got: {log_output}"
    )
    
    # Verify the function returned False (limit exceeded)
    assert is_within_limit is False, (
        f"Expected check_wall_time_limit to return False when limit exceeded, got {is_within_limit}"
    )
    
    logger.info("Contract test PASSED: Timeout handler logs TIMEOUT_WARNING correctly.")

@pytest.mark.contract
def test_timeout_handler_within_limit():
    """
    Contract test: Verify that the timeout handler returns True and does NOT log
    a warning when within the time limit.
    """
    logger = get_logger(__name__)
    
    # Set a timeout of 100 seconds
    test_timeout_seconds = 100.0
    
    # Start time is now
    start_time = time.time()
    
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)
    
    is_within_limit = check_wall_time_limit(start_time, test_timeout_seconds)
    
    log_output = log_stream.getvalue()
    
    # Verify no warning was logged
    assert "TIMEOUT_WARNING" not in log_output, (
        f"Did not expect 'TIMEOUT_WARNING' when within limit, but got: {log_output}"
    )
    
    # Verify the function returned True
    assert is_within_limit is True, (
        f"Expected check_wall_time_limit to return True when within limit, got {is_within_limit}"
    )
    
    logger.info("Contract test PASSED: Timeout handler correctly identifies within-limit state.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])