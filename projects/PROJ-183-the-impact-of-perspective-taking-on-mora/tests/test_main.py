"""
Unit tests for main.py resource monitoring functionality.
"""
import os
import sys
import time
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

import main

def test_get_peak_ram_gb():
    """Test that get_peak_ram_gb returns a non-negative number."""
    ram = main.get_peak_ram_gb()
    assert isinstance(ram, float)
    assert ram >= 0.0

def test_log_resource_metrics_logs_to_file():
    """Test that log_resource_metrics writes to the configured log file."""
    # Create a temporary directory for logs
    temp_dir = tempfile.mkdtemp()
    try:
        log_file = os.path.join(temp_dir, "test_metrics.log")
        
        # Patch the log_file path
        with patch.object(main, 'log_file', log_file):
            # Reconfigure logging to use the temp file
            for handler in logging.getLogger().handlers[:]:
                logging.getLogger().removeHandler(handler)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            logger = logging.getLogger(__name__)
            
            # Run the function
            start = time.time() - 1  # Pretend we ran for 1 second
            main.log_resource_metrics(start)
            
            # Verify file exists and has content
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Current Runtime" in content
                assert "Peak RAM Usage" in content
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

def test_main_execution_creates_log_file():
    """Test that main() creates the log file and writes final metrics."""
    temp_dir = tempfile.mkdtemp()
    try:
        log_dir = os.path.join(temp_dir, "data", "logs")
        log_file = os.path.join(log_dir, "resource_metrics.log")
        
        # Ensure the directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Patch the log_dir and log_file
        with patch.object(main, 'log_dir', log_dir):
            with patch.object(main, 'log_file', log_file):
                # Reconfigure logging
                for handler in logging.getLogger().handlers[:]:
                    logging.getLogger().removeHandler(handler)
                
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler(sys.stdout)
                    ]
                )
                
                # Mock the sleep to make test fast
                with patch('time.sleep', return_value=None):
                    main.main()
                
                # Verify file exists and contains final metrics
                assert os.path.exists(log_file), f"Log file {log_file} was not created"
                
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert "PIPELINE EXECUTION COMPLETE" in content
                    assert "Total Runtime" in content
                    assert "Final Peak RAM" in content
                    assert "Log file location" in content
    finally:
        shutil.rmtree(temp_dir)