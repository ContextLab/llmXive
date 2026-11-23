import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.logging_config import (
    setup_logging,
    get_module_logger,
    log_operation_start,
    log_operation_complete,
    log_data_filter_step,
    log_skipped_row,
    log_zero_variance_field,
    log_model_convergence,
    log_file_write
)

def test_logging_integration():
    """
    Test that logging functions write to the log file and console.
    """
    # Setup a temporary log directory
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "test.log")
    
    try:
        # Setup logging to temp file
        setup_logging(log_file="test.log")
        
        # Get logger
        logger = get_module_logger("test_module")
        
        # Test log operations
        log_operation_start(logger, "Test Operation")
        log_data_filter_step(logger, "source", "target", 100, 90, "Test reason")
        log_skipped_row(logger, 5, "col1")
        log_zero_variance_field(logger, "field_x", 1)
        log_model_convergence(logger, "TestModel", True)
        log_file_write(logger, "/path/to/file.csv", "data")
        log_operation_complete(logger, "Test Operation", success=True)
        
        # Verify log file exists and has content
        full_log_path = os.path.join(temp_dir, "test.log")
        assert os.path.exists(full_log_path), "Log file not created"
        
        with open(full_log_path, 'r') as f:
            content = f.read()
            assert "Test Operation" in content
            assert "FILTER STEP" in content
            assert "Skipping row" in content
            assert "Zero variance" in content
            assert "CONVERGED" in content
            assert "FILE WRITTEN" in content
            assert "COMPLETED OPERATION" in content
            
        print("Logging integration test passed.")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_logging_integration()