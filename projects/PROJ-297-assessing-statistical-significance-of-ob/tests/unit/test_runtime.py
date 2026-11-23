import time
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from main import handle_timeout, write_runtime_log, RUNTIME_LIMIT_SECONDS
import logging

class TestRuntimeMeasurement(unittest.TestCase):
    
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
    def test_handle_timeout_within_limit(self):
        """Test that handle_timeout does not raise when within limit."""
        # Mock time to be well within the limit
        with patch('time.time', return_value=self.start_time + 100):
            elapsed = handle_timeout(self.start_time, self.logger)
            self.assertLess(elapsed, RUNTIME_LIMIT_SECONDS)
            
    def test_handle_timeout_exceeds_limit(self):
        """Test that handle_timeout raises TimeoutError when limit exceeded."""
        # Mock time to be beyond the limit
        with patch('time.time', return_value=self.start_time + RUNTIME_LIMIT_SECONDS + 100):
            with self.assertRaises(TimeoutError):
                handle_timeout(self.start_time, self.logger)
                
    def test_write_runtime_log_creates_file(self):
        """Test that write_runtime_log creates the log file."""
        # Mock the path to avoid writing to actual location during test
        with patch('main.RUNTIME_LOG_PATH', '/tmp/test_runtime_log.json'):
            write_runtime_log(100.0, "success", self.logger)
            
            # Verify file was created
            self.assertTrue(os.path.exists('/tmp/test_runtime_log.json'))
            
            # Verify content
            import json
            with open('/tmp/test_runtime_log.json', 'r') as f:
                data = json.load(f)
                
            self.assertEqual(data['elapsed_seconds'], 100.0)
            self.assertEqual(data['status'], 'success')
            self.assertIn('timestamp', data)
            
    def test_runtime_limit_constant(self):
        """Test that the runtime limit is set to 6 hours."""
        self.assertEqual(RUNTIME_LIMIT_SECONDS, 21600)

if __name__ == '__main__':
    unittest.main()