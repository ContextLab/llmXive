import os
import sys
import json
import time
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.resource_monitor import (
    get_peak_memory_gb,
    check_resource_constraints,
    log_resource_usage,
    MAX_EXECUTION_TIME_SECONDS,
    MAX_MEMORY_GB
)
from utils.error_codes import ErrorCode

class TestResourceMonitor(unittest.TestCase):
    
    def test_get_peak_memory_gb_returns_positive(self):
        """Test that get_peak_memory_gb returns a positive float."""
        memory = get_peak_memory_gb()
        self.assertIsInstance(memory, float)
        self.assertGreater(memory, 0.0)

    def test_check_resource_constraints_pass(self):
        """Test that constraints pass when within limits."""
        # 1 hour, 1 GB
        result = check_resource_constraints(3600, 1.0)
        self.assertTrue(result)

    def test_check_resource_constraints_fail_time(self):
        """Test that constraints fail when time exceeds limit."""
        # 5 hours, 1 GB
        with patch('utils.resource_monitor.log_error') as mock_log:
            result = check_resource_constraints(5 * 3600, 1.0)
            self.assertFalse(result)
            mock_log.assert_called_once()
            # Verify error code is used
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], ErrorCode.INSUFFICIENT_POWER)

    def test_check_resource_constraints_fail_memory(self):
        """Test that constraints fail when memory exceeds limit."""
        # 1 hour, 8 GB
        with patch('utils.resource_monitor.log_error') as mock_log:
            result = check_resource_constraints(3600, 8.0)
            self.assertFalse(result)
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], ErrorCode.INSUFFICIENT_POWER)

    def test_log_resource_usage_creates_file(self):
        """Test that log_resource_usage creates the JSON file."""
        output_path = "data/artifacts/resource_log.json"
        # Ensure directory exists
        os.makedirs("data/artifacts", exist_ok=True)
        
        # Remove file if exists
        if os.path.exists(output_path):
            os.remove(output_path)

        log_resource_usage(100.5, 2.3)

        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["execution_time_seconds"], 100.5)
        self.assertEqual(data["peak_memory_gb"], 2.3)

    def test_log_resource_usage_overwrites_file(self):
        """Test that log_resource_usage overwrites existing file."""
        output_path = "data/artifacts/resource_log.json"
        os.makedirs("data/artifacts", exist_ok=True)
        
        # Write initial data
        with open(output_path, 'w') as f:
            json.dump({"execution_time_seconds": 1.0, "peak_memory_gb": 1.0}, f)

        log_resource_usage(200.0, 4.0)

        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["execution_time_seconds"], 200.0)
        self.assertEqual(data["peak_memory_gb"], 4.0)

if __name__ == "__main__":
    unittest.main()