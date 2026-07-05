"""
Unit tests for OULAD URL accessibility and response validation.

This module verifies that the configured OULAD dataset URL is accessible
and that the HTTP response meets validation criteria (status code, content type,
and basic size checks) before attempting to download or process the data.

Tests:
    - test_oulad_url_accessible: Verifies the URL returns a 200 OK status.
    - test_oulad_response_content_type: Verifies the response is a valid archive (gzip/tar).
    - test_oulad_response_minimum_size: Verifies the response is not empty (size > 1KB).
    - test_oulad_config_url_exists: Verifies the URL is defined in config.py.
"""

import os
import sys
import unittest
import requests
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import load_config, get_config_value


class TestOuladUrlAccessibility(unittest.TestCase):
    """Test cases for OULAD URL accessibility and response validation."""

    @classmethod
    def setUpClass(cls):
        """
        Load configuration once for all tests.
        Raises an exception if the config cannot be loaded.
        """
        try:
            cls.config = load_config()
            cls.oulad_url = get_config_value(cls.config, 'dataset', 'oulad_url')
        except Exception as e:
            # If config fails, skip all tests in this class
            raise unittest.SkipTest(f"Configuration loading failed: {e}")

    def test_oulad_config_url_exists(self):
        """
        Verify that the OULAD URL is defined in the configuration file.
        """
        self.assertIsNotNone(self.oulad_url, "OULAD URL is not defined in config")
        self.assertIsInstance(self.oulad_url, str, "OULAD URL must be a string")
        self.assertTrue(self.oulad_url.startswith("http"), "OULAD URL must start with http/https")

    def test_oulad_url_accessible(self):
        """
        Verify that the OULAD URL is accessible and returns a 200 OK status.
        
        This test ensures the external data source is reachable.
        """
        try:
            response = requests.get(self.oulad_url, timeout=30)
        except requests.exceptions.Timeout:
            self.fail(f"Request to {self.oulad_url} timed out after 30 seconds")
        except requests.exceptions.ConnectionError:
            self.fail(f"Connection error while trying to reach {self.oulad_url}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Unexpected request error: {e}")

        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code} for URL: {self.oulad_url}"
        )

    def test_oulad_response_content_type(self):
        """
        Verify that the response content type indicates a valid archive.
        
        OULAD data is typically distributed as a .tar.gz file.
        We check for 'gzip', 'tar', or 'octet-stream' content types.
        """
        try:
            response = requests.get(self.oulad_url, timeout=30)
        except requests.exceptions.RequestException:
            self.fail("Failed to fetch URL for content type check")

        content_type = response.headers.get('Content-Type', '').lower()
        content_disposition = response.headers.get('Content-Disposition', '').lower()

        # Check if it looks like a compressed archive
        is_valid_archive = (
            'gzip' in content_type or
            'x-gzip' in content_type or
            'tar' in content_type or
            'octet-stream' in content_type or
            '.tar.gz' in content_disposition or
            '.tgz' in content_disposition
        )

        self.assertTrue(
            is_valid_archive,
            f"Response does not appear to be an archive. "
            f"Content-Type: {content_type}, "
            f"Content-Disposition: {content_disposition}"
        )

    def test_oulad_response_minimum_size(self):
        """
        Verify that the response body is not empty (size > 1KB).
        
        This prevents downloading corrupted or placeholder 0-byte files.
        """
        try:
            response = requests.get(self.oulad_url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            self.fail("Failed to fetch URL for size check")

        # Check content length header or actual content length
        content_length = response.headers.get('Content-Length')
        actual_size = len(response.content)

        if content_length:
            expected_size = int(content_length)
            # Allow a small margin of error if the header is approximate
            self.assertGreater(
                expected_size,
                1024,
                f"Content-Length header ({expected_size}) indicates file is too small (< 1KB)"
            )

        # Verify actual downloaded size
        self.assertGreater(
            actual_size,
            1024,
            f"Actual downloaded content size ({actual_size} bytes) is too small (< 1KB). "
            f"URL: {self.oulad_url}"
        )


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)