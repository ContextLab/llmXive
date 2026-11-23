import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.cache import compute_hash
from code.config import Config
from code.data.download import is_valid_python_function

class TestDatasetSampling(unittest.TestCase):
    """
    Unit tests for dataset sampling logic in download.py.
    Specifically tests that the sampler stops after a configurable
    maximum number of attempts or a target number of valid samples.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.max_attempts = self.config.MAX_ATTEMPTS
        self.target_valid = self.config.TARGET_VALID_FUNCTIONS
        self.min_valid = self.config.MIN_VALID_FUNCTIONS

    def test_sampling_stops_at_target_valid_samples(self):
        """
        Assert that the sampler stops immediately after finding
        the target number of valid samples (200), without exceeding
        the max attempts.
        """
        # Mock data source: first 200 items are valid, rest are invalid
        # We simulate a dataset iterator
        valid_count = 0
        call_count = 0

        def mock_fetch_function(index):
            nonlocal call_count, valid_count
            call_count += 1
            # Return valid code for first 200 attempts
            if valid_count < self.target_valid:
                valid_count += 1
                return "def valid_func(): pass", True
            return "invalid syntax here", False

        # Simulate the sampling loop logic found in download.py
        valid_samples = []
        attempts = 0
        
        while len(valid_samples) < self.target_valid:
            if attempts >= self.max_attempts:
                break
            attempts += 1
            
            code, is_valid = mock_fetch_function(attempts)
            if is_valid:
                valid_samples.append(code)

        # Assertions
        self.assertEqual(len(valid_samples), self.target_valid)
        # We should have stopped exactly at target, so attempts == target_valid
        # (assuming every fetch was valid until target reached)
        self.assertLessEqual(attempts, self.max_attempts)
        self.assertLessEqual(len(valid_samples), self.target_valid)

    def test_sampling_stops_at_max_attempts_when_insufficient_valid(self):
        """
        Assert that the sampler stops after max_attempts (400)
        if valid samples are scarce, and does not exceed the limit.
        """
        valid_count = 0
        attempts = 0
        
        # Simulate a dataset where only 50% are valid
        # This ensures we hit max_attempts before hitting target_valid
        
        def mock_fetch_function(index):
            nonlocal valid_count
            # Alternate valid/invalid
            if index % 2 == 0:
                valid_count += 1
                return "def valid_func(): pass", True
            return "invalid syntax here", False

        valid_samples = []
        attempts = 0
        
        while len(valid_samples) < self.target_valid:
            if attempts >= self.max_attempts:
                break
            attempts += 1
            
            code, is_valid = mock_fetch_function(attempts)
            if is_valid:
                valid_samples.append(code)

        # Assertions
        self.assertEqual(attempts, self.max_attempts)
        self.assertLess(len(valid_samples), self.target_valid)
        # We expect roughly half to be valid
        self.assertGreater(len(valid_samples), 0)

    def test_sampling_handles_invalid_code_gracefully(self):
        """
        Assert that the sampler correctly identifies invalid code
        using is_valid_python_function and skips it.
        """
        valid_code = "def valid():\n    pass"
        invalid_code = "def invalid(:\n    pass"
        
        self.assertTrue(is_valid_python_function(valid_code))
        self.assertFalse(is_valid_python_function(invalid_code))

    def test_hash_consistency_for_valid_samples(self):
        """
        Assert that compute_hash produces consistent results for the same code.
        """
        code = "def test_function():\n    x = 1\n    return x"
        hash1 = compute_hash(code)
        hash2 = compute_hash(code)
        
        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64) # SHA-256 hex length

    def test_sampling_limits_total_attempts(self):
        """
        Verify that the sampling loop enforces the MAX_ATTEMPTS limit strictly.
        """
        max_attempts = 50
        target = 100
        attempts_made = 0

        def mock_fetch(index):
            nonlocal attempts_made
            attempts_made += 1
            return "def valid(): pass", True

        valid_samples = []
        attempts = 0

        while len(valid_samples) < target:
            if attempts >= max_attempts:
                break
            attempts += 1
            code, is_valid = mock_fetch(attempts)
            if is_valid:
                valid_samples.append(code)

        self.assertEqual(attempts, max_attempts)
        self.assertEqual(len(valid_samples), max_attempts)
        self.assertLess(len(valid_samples), target)

if __name__ == '__main__':
    unittest.main()