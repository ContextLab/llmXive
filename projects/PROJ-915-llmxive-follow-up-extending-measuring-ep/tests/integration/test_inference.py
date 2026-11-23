"""
Integration test for inference timeout handling (Task T019).

This test verifies that the inference pipeline correctly handles timeout scenarios
by raising the appropriate exception (InferenceTimeoutError) and ensuring
the error handling framework functions as designed.

It uses the real error handling framework from code/error_handling.py.
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.error_handling import (
    InferenceTimeoutError,
    run_inference_with_timeout,
    enforce_inference_timeout,
    timeout_context
)
from code.config import get_config


class TestInferenceTimeoutHandling(unittest.TestCase):
    """
    Integration tests for the inference timeout mechanism.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = get_config()
        # Default timeout for testing is very short to ensure fast execution
        cls.test_timeout = 2.0

    def test_timeout_context_raises_on_slow_operation(self):
        """
        Test that the timeout_context manager raises InferenceTimeoutError
        when a simulated operation exceeds the time limit.
        """
        def slow_operation():
            time.sleep(3.0)  # Sleep longer than the timeout

        with self.assertRaises(InferenceTimeoutError):
            with timeout_context(timeout=self.test_timeout, operation_name="slow_test_op"):
                slow_operation()

    def test_timeout_context_passes_on_fast_operation(self):
        """
        Test that the timeout_context manager allows operations to complete
        successfully if they finish within the time limit.
        """
        result = []
        def fast_operation():
            time.sleep(0.5)  # Sleep less than the timeout
            result.append("completed")

        start = time.time()
        with timeout_context(timeout=self.test_timeout, operation_name="fast_test_op"):
            fast_operation()
        end = time.time()

        self.assertEqual(result, ["completed"])
        self.assertLess(end - start, 2.0)

    @patch('code.error_handling.subprocess.run')
    def test_run_inference_with_timeout_mocked_process(self, mock_run):
        """
        Test run_inference_with_timeout with a mocked subprocess that times out.
        """
        # Simulate a process that hangs
        mock_process = MagicMock()
        mock_process.wait.side_effect = TimeoutError("Process timed out")
        mock_run.return_value = mock_process

        def dummy_inference_func():
            # Simulate the internal logic that would call subprocess
            raise TimeoutError("Inference process timed out")

        with self.assertRaises(InferenceTimeoutError):
            run_inference_with_timeout(
                inference_func=dummy_inference_func,
                timeout=self.test_timeout,
                model_name="test-model"
            )

    def test_enforce_inference_timeout_signal_handling(self):
        """
        Test that enforce_inference_timeout correctly sets up signal handlers.
        This test verifies the mechanism exists and raises the error.
        """
        def hanging_func():
            while True:
                time.sleep(0.1)

        with self.assertRaises(InferenceTimeoutError):
            enforce_inference_timeout(
                func=hanging_func,
                timeout=self.test_timeout,
                args=(),
                kwargs={}
            )

    def test_timeout_error_message_content(self):
        """
        Verify that InferenceTimeoutError contains relevant context in its message.
        """
        try:
            with timeout_context(timeout=0.1, operation_name="test_op"):
                time.sleep(1.0)
        except InferenceTimeoutError as e:
            self.assertIn("test_op", str(e))
            self.assertIn("timeout", str(e).lower())


if __name__ == '__main__':
    unittest.main()