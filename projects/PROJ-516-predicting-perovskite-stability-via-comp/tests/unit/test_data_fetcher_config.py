"""
Unit tests for T006: Data fetcher retry logic configuration.

Verifies that:
1. config.yaml contains the 'delay_multiplier' key.
2. data_fetcher.py reads and uses the 'delay_multiplier' from config.
3. Exponential backoff logic follows the formula: base_delay * (delay_multiplier ^ retry_count).
"""
import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import yaml

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.data_fetcher import fetch_with_retry, FetchError, _load_config
from urllib.error import URLError

class TestDataFetcherConfig(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.config_path = Path(__file__).parent.parent.parent / "code" / "config.yaml"
        self.original_config = None
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.original_config = yaml.safe_load(f)

    def tearDown(self):
        """Restore original config."""
        if self.original_config is not None:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.original_config, f)
        elif self.config_path.exists():
            self.config_path.unlink()

    def test_config_contains_delay_multiplier(self):
        """Verify config.yaml contains delay_multiplier key."""
        config = _load_config()
        self.assertIn('delay_multiplier', config)
        self.assertIsInstance(config['delay_multiplier'], float)
        self.assertGreater(config['delay_multiplier'], 1.0)

    def test_delay_multiplier_is_used(self):
        """Verify that the delay_multiplier is actually used in the retry logic."""
        # Mock urlopen to always fail
        with patch('utils.data_fetcher.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = URLError("Simulated network error")

            # Use small delays to test quickly
            # base=0.01, multiplier=3.0 -> delays: 0.01, 0.03, 0.09
            start_time = time.time()
            with self.assertRaises(FetchError):
                fetch_with_retry(
                    "http://example.com/test",
                    max_retries=2,
                    base_delay=0.01,
                    delay_multiplier=3.0,
                    max_delay=1.0,
                    timeout=0.1
                )
            elapsed = time.time() - start_time

            # Expected delays: 0.01 (after attempt 1) + 0.03 (after attempt 2) = 0.04s
            # We allow some tolerance for execution time
            self.assertGreater(elapsed, 0.03)  # Must be at least sum of delays
            self.assertLess(elapsed, 0.2)  # Should not take too long

    def test_exponential_backoff_formula(self):
        """Verify the exponential backoff formula: delay = base * (multiplier ^ retry)."""
        # We test the internal logic by checking the delay sequence
        # base=1.0, multiplier=2.0 -> delays: 1.0, 2.0, 4.0
        # We mock time.sleep to capture the values
        captured_delays = []
        
        with patch('utils.data_fetcher.urlopen') as mock_urlopen, \
             patch('utils.data_fetcher.time.sleep') as mock_sleep:
            
            mock_urlopen.side_effect = URLError("Simulated error")
            mock_sleep.side_effect = lambda d: captured_delays.append(d)

            with self.assertRaises(FetchError):
                fetch_with_retry(
                    "http://example.com/test",
                    max_retries=2,
                    base_delay=1.0,
                    delay_multiplier=2.0,
                    max_delay=10.0,
                    timeout=0.1
                )

            # Expected delays: 1.0 * (2^1) = 2.0? 
            # Wait, let's re-read the code logic:
            # current_delay starts at base_delay (1.0)
            # After attempt 0 (first fail), we sleep current_delay (1.0)
            # Then update: current_delay = base * (multiplier ^ (attempt+1)) = 1 * (2^1) = 2.0
            # After attempt 1 (second fail), we sleep current_delay (2.0)
            # Then update: current_delay = 1 * (2^2) = 4.0
            # After attempt 2 (third fail), we stop (max_retries=2, so 3 attempts total)
            
            # So captured_delays should be [1.0, 2.0]
            self.assertEqual(len(captured_delays), 2)
            self.assertEqual(captured_delays[0], 1.0)
            self.assertEqual(captured_delays[1], 2.0)

    def test_config_loading_from_file(self):
        """Verify that _load_config reads from config.yaml correctly."""
        # Create a temporary config with specific values
        test_config = {
            "max_retries": 5,
            "base_delay": 0.5,
            "delay_multiplier": 1.5,
            "max_delay": 30.0,
            "timeout": 10.0
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)

        loaded = _load_config()
        
        self.assertEqual(loaded['max_retries'], 5)
        self.assertEqual(loaded['base_delay'], 0.5)
        self.assertEqual(loaded['delay_multiplier'], 1.5)
        self.assertEqual(loaded['max_delay'], 30.0)
        self.assertEqual(loaded['timeout'], 10.0)

    def test_default_values_when_config_missing(self):
        """Verify default values are used when config.yaml is missing."""
        # Remove config if it exists
        if self.config_path.exists():
            self.config_path.unlink()

        loaded = _load_config()
        
        # Check defaults
        self.assertEqual(loaded['max_retries'], 3)
        self.assertEqual(loaded['base_delay'], 1.0)
        self.assertEqual(loaded['delay_multiplier'], 2.0)
        self.assertEqual(loaded['max_delay'], 60.0)
        self.assertEqual(loaded['timeout'], 30.0)

if __name__ == '__main__':
    unittest.main()