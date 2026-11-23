"""
Verify timeout handling for Khan Academy dataset fetch.

This script simulates a network timeout during the Khan Academy dataset fetch
and verifies that the system exits with code 1 and logs the exact required
error message as specified in FR-007.

Deliverable: Test log confirming exit code and message.
Dependency: T012c
"""

import os
import sys
import time
import json
import logging
import tempfile
from unittest.mock import patch, MagicMock
from io import StringIO

# Configure logging to capture output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Import the actual fetch function to test
# We need to mock the datasets.load_dataset to simulate timeout
from download.fetch_khan_academy import fetch_khan_academy_dataset, TimeoutError


def run_timeout_test():
    """
    Simulate a timeout during Khan Academy dataset fetch and verify behavior.
    """
    logger.info("Starting timeout simulation test for Khan Academy dataset fetch...")
    
    # Track log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Mock the datasets.load_dataset to raise a timeout error
    original_load_dataset = None
    try:
        from datasets import load_dataset
        original_load_dataset = load_dataset
    except ImportError:
        logger.error("datasets library not found. Cannot run test.")
        return False
    
    def mock_timeout_load_dataset(*args, **kwargs):
        """Simulate a timeout during dataset loading."""
        raise TimeoutError("Simulated network timeout during dataset fetch")
    
    # Patch the load_dataset function
    with patch('download.fetch_khan_academy.load_dataset', side_effect=mock_timeout_load_dataset):
        try:
            # Attempt to fetch the dataset - this should trigger the timeout handling
            fetch_khan_academy_dataset()
            logger.error("ERROR: Expected TimeoutError was not raised. Test failed.")
            return False
        except SystemExit as e:
            # Verify exit code is 1
            if e.code != 1:
                logger.error(f"ERROR: Expected exit code 1, got {e.code}. Test failed.")
                return False
            
            # Capture the log output
            log_output = log_capture.getvalue()
            
            # Verify the exact error message is present
            expected_message = "ERROR: Failed to download Khan Academy dataset within 300 seconds – aborting pipeline."
            
            if expected_message not in log_output:
                logger.error(f"ERROR: Expected message not found in logs.")
                logger.error(f"Expected: {expected_message}")
                logger.error(f"Actual logs: {log_output}")
                return False
            
            logger.info("SUCCESS: Timeout handling verified correctly.")
            logger.info(f"Exit code: {e.code}")
            logger.info(f"Log message verified: '{expected_message}'")
            
            # Save test result to a log file
            test_result = {
                "test_name": "verify_timeout_handling_khan",
                "status": "PASS",
                "exit_code": 1,
                "message_verified": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "expected_message": expected_message
            }
            
            # Ensure output directory exists
            os.makedirs("data/logs", exist_ok=True)
            result_file = "data/logs/timeout_test_khan.json"
            
            with open(result_file, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            logger.info(f"Test result saved to: {result_file}")
            return True
        except Exception as e:
            logger.error(f"ERROR: Unexpected exception during test: {type(e).__name__}: {e}")
            return False
        finally:
            # Remove our handler
            logger.removeHandler(handler)


def main():
    """Main entry point for the timeout verification script."""
    logger.info("=" * 60)
    logger.info("Khan Academy Dataset Timeout Handling Verification")
    logger.info("=" * 60)
    
    success = run_timeout_test()
    
    if success:
        logger.info("TEST PASSED: Timeout handling works as expected.")
        sys.exit(0)
    else:
        logger.error("TEST FAILED: Timeout handling did not work as expected.")
        sys.exit(1)


if __name__ == "__main__":
    main()