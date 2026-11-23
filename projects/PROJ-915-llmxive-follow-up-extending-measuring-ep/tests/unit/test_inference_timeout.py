"""
Unit tests for the inference timeout enforcement mechanism (T020a).
"""
import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inference import generate_with_timeout, log_timeout_failure
from error_handling import InferenceTimeoutError
import logging

# Configure logging to avoid errors during tests
logging.basicConfig(level=logging.WARNING)

class MockModel:
    """Mock model that simulates slow or fast generation."""
    def __init__(self, delay: float = 0.1, fail: bool = False):
        self.delay = delay
        self.fail = fail

    def __call__(self, prompt, **kwargs):
        if self.fail:
            raise ValueError("Simulated model error")
        time.sleep(self.delay)
        return {"choices": [{"text": "Mock response"}]}

class TestInferenceTimeout(unittest.TestCase):
    
    def setUp(self):
        # Ensure log file exists or is handled
        self.log_path = "data/interim/timeout_failures.log"
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_fast_generation_success(self):
        """Test that a fast generation completes successfully."""
        model = MockModel(delay=0.1)
        result = generate_with_timeout(
            model, 
            "Test prompt", 
            timeout_seconds=5.0, 
            prompt_id="test_001"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result, "Mock response")

    def test_timeout_enforcement(self):
        """Test that a slow generation raises InferenceTimeoutError."""
        # Model takes 3 seconds, timeout is 1 second
        model = MockModel(delay=3.0)
        
        with self.assertRaises(InferenceTimeoutError) as context:
            generate_with_timeout(
                model,
                "Slow prompt",
                timeout_seconds=1.0,
                prompt_id="slow_001"
            )
        
        self.assertIn("timed out", str(context.exception).lower())
        
        # Verify log file was written
        self.assertTrue(os.path.exists(self.log_path))
        with open(self.log_path, 'r') as f:
            content = f.read()
            self.assertIn("slow_001", content)
            self.assertIn("exceeded", content)

    def test_model_error_propagation(self):
        """Test that model errors are propagated correctly."""
        model = MockModel(fail=True)
        
        with self.assertRaises(ValueError) as context:
            generate_with_timeout(
                model,
                "Error prompt",
                timeout_seconds=5.0,
                prompt_id="error_001"
            )
        
        self.assertEqual(str(context.exception), "Simulated model error")

    def test_timeout_logging_format(self):
        """Test that the log entry contains required fields."""
        model = MockModel(delay=2.0)
        try:
            generate_with_timeout(
                model,
                "Log test",
                timeout_seconds=0.5,
                prompt_id="log_test_001"
            )
        except InferenceTimeoutError:
            pass

        with open(self.log_path, 'r') as f:
            content = f.read()
            self.assertIn("PROMPT_ID=log_test_001", content)
            self.assertIn("DURATION=", content)

if __name__ == '__main__':
    unittest.main()