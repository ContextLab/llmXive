import os
import sys
import unittest
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from test_executor import (
    _jacoco_agent_active,
    _last_jacoco_output_dir,
    _reset_jacoco_agent_state,
    ExecutionResult,
    enforce_test_timeout,
    run_with_jacoco,
    CompilationFailedError
)

class TestJacocoResetAfterTimeout(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.jacoco_exec_path = os.path.join(self.temp_dir, "jacoco.exec")
        # Create a dummy jacoco.exec file to simulate existing state
        with open(self.jacoco_exec_path, 'w') as f:
            f.write("dummy data")
        
        # Simulate active state
        import test_executor
        test_executor._jacoco_agent_active = True
        test_executor._last_jacoco_output_dir = self.temp_dir

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        # Reset state
        import test_executor
        test_executor._jacoco_agent_active = False
        test_executor._last_jacoco_output_dir = None

    @patch('subprocess.Popen')
    def test_jacoco_reset_after_timeout(self, mock_popen):
        """
        Verifies that if a test times out, the JaCoCo agent state is cleared
        and the jacoco.exec file is removed to prevent state leakage.
        """
        # Mock the process to simulate a timeout
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Configure communicate to raise TimeoutExpired
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="java ...", timeout=30)
        
        # Call the function
        result = run_with_jacoco(
            test_class="com.example.Test",
            class_path="/tmp/classes",
            jacoco_agent_path="/tmp/jacoco.jar",
            output_dir=self.temp_dir,
            timeout=30
        )
        
        # Verify the result indicates timeout
        self.assertFalse(result.success)
        self.assertEqual(result.status, "timeout")
        self.assertTrue(result.timeout)
        
        # Verify the jacoco.exec file was removed
        self.assertFalse(os.path.exists(self.jacoco_exec_path))
        
        # Verify the internal state was reset
        import test_executor
        self.assertFalse(test_executor._jacoco_agent_active)
        self.assertIsNone(test_executor._last_jacoco_output_dir)

    def test_reset_function_removes_file(self):
        """
        Verifies that the internal _reset_jacoco_agent_state function
        explicitly removes the jacoco.exec file.
        """
        # Ensure file exists
        self.assertTrue(os.path.exists(self.jacoco_exec_path))
        
        # Call reset
        _reset_jacoco_agent_state()
        
        # Verify file is gone
        self.assertFalse(os.path.exists(self.jacoco_exec_path))
        
        # Verify state flags
        self.assertFalse(_jacoco_agent_active)
        self.assertIsNone(_last_jacoco_output_dir)

if __name__ == '__main__':
    unittest.main()