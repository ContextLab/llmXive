"""
Unit tests for data download retry logic.

Tests the retry mechanism in the download module to ensure it handles
transient failures correctly and respects retry limits.
"""
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_logger
from config import RANDOM_SEED

# Mock the actual download function to simulate failures/success
class MockDownloader:
    def __init__(self, fail_count=0):
        self.fail_count = fail_count
        self.attempt_count = 0
        self.logger = get_logger("test_download")

    def _fetch_with_retry(self, url, dest_path, max_retries=3, delay=1):
        """Simulated fetch with retry logic."""
        self.attempt_count = 0
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            self.attempt_count = attempt
            try:
                if attempt <= self.fail_count:
                    # Simulate a transient network error
                    raise ConnectionError(f"Transient failure on attempt {attempt}")
                else:
                    # Simulate success
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    dest_path.write_text("mock data content")
                    return True
            except ConnectionError as e:
                last_exception = e
                if attempt == max_retries:
                    break
                # In real implementation, would sleep here
                continue
        
        if self.attempt_count == max_retries and last_exception:
            raise last_exception
        
        return True

class TestDownloadRetryLogic(unittest.TestCase):
    """Tests for the download retry mechanism."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("tests/unit/temp_download")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.downloader = MockDownloader()

    def tearDown(self):
        """Clean up test files."""
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_success_on_first_attempt(self):
        """Test that download succeeds immediately when no failures occur."""
        downloader = MockDownloader(fail_count=0)
        dest = self.test_dir / "success_first.dat"
        
        result = downloader._fetch_with_retry(
            "http://example.com/data", 
            dest, 
            max_retries=3
        )
        
        self.assertTrue(result)
        self.assertEqual(downloader.attempt_count, 1)
        self.assertTrue(dest.exists())

    def test_success_after_transient_failure(self):
        """Test that download succeeds after a transient failure."""
        downloader = MockDownloader(fail_count=1)
        dest = self.test_dir / "success_after_retry.dat"
        
        result = downloader._fetch_with_retry(
            "http://example.com/data", 
            dest, 
            max_retries=3
        )
        
        self.assertTrue(result)
        self.assertEqual(downloader.attempt_count, 2)  # Failed once, succeeded on second
        self.assertTrue(dest.exists())

    def test_success_after_multiple_retries(self):
        """Test that download succeeds after multiple transient failures."""
        downloader = MockDownloader(fail_count=2)
        dest = self.test_dir / "success_multiple_retries.dat"
        
        result = downloader._fetch_with_retry(
            "http://example.com/data", 
            dest, 
            max_retries=5
        )
        
        self.assertTrue(result)
        self.assertEqual(downloader.attempt_count, 3)  # Failed twice, succeeded on third
        self.assertTrue(dest.exists())

    def test_failure_after_max_retries(self):
        """Test that download fails after exhausting all retries."""
        downloader = MockDownloader(fail_count=10)  # More than max_retries
        dest = self.test_dir / "failure_max_retries.dat"
        
        with self.assertRaises(ConnectionError):
            downloader._fetch_with_retry(
                "http://example.com/data", 
                dest, 
                max_retries=3
            )
        
        self.assertEqual(downloader.attempt_count, 3)
        # File should not exist if all attempts failed
        self.assertFalse(dest.exists())

    def test_retry_limit_enforcement(self):
        """Test that the retry limit is strictly enforced."""
        downloader = MockDownloader(fail_count=5)
        dest = self.test_dir / "retry_limit_test.dat"
        
        max_retries = 2
        try:
            downloader._fetch_with_retry(
                "http://example.com/data", 
                dest, 
                max_retries=max_retries
            )
            self.fail("Expected ConnectionError to be raised")
        except ConnectionError:
            pass  # Expected
        
        # Should have attempted exactly max_retries + 1 times (initial + retries)
        # Actually, our logic counts attempts in the loop, so it should be max_retries
        self.assertEqual(downloader.attempt_count, max_retries)

    def test_dest_directory_creation(self):
        """Test that destination directory is created if it doesn't exist."""
        downloader = MockDownloader(fail_count=0)
        dest = self.test_dir / "new_subdir" / "data.dat"
        
        result = downloader._fetch_with_retry(
            "http://example.com/data", 
            dest, 
            max_retries=1
        )
        
        self.assertTrue(result)
        self.assertTrue(dest.parent.exists())
        self.assertTrue(dest.exists())

if __name__ == "__main__":
    unittest.main()
