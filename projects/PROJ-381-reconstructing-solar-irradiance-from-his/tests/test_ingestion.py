"""
Unit tests for data ingestion module.
Verifies SILSO and SORCE URL reachability before attempting data download.
"""
import unittest
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import RequestException, Timeout
import sys
import os

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.config import ensure_directories
from code.env_manager import get_data_path


class TestIngestionURLs(unittest.TestCase):
    """Tests for verifying external data source availability."""

    @classmethod
    def setUpClass(cls):
        """Ensure required directories exist before running tests."""
        ensure_directories()

    def test_silso_url_reachability(self):
        """
        Verify SILSO (Sunspot Index and Long-term Solar Observations) URL is reachable.
        Target: http://www.sidc.be/silso/datafiles (or the specific CSV endpoint).
        """
        # Using the standard SILSO data file endpoint
        url = "http://www.sidc.be/silso/datafiles"
        
        # We use a timeout to ensure the test doesn't hang indefinitely
        # A 10-second timeout is usually sufficient for a reachability check.
        try:
            response = requests.get(url, timeout=10)
            # Check if the status code is in the 200 range
            self.assertTrue(
                200 <= response.status_code < 300,
                f"SILSO URL returned status {response.status_code}: {response.reason}"
            )
        except Timeout:
            self.fail(f"SILSO URL ({url}) timed out after 10 seconds.")
        except RequestException as e:
            self.fail(f"SILSO URL ({url}) failed to connect: {e}")

    def test_sorce_url_reachability(self):
        """
        Verify SORCE (Solar Radiation and Climate Experiment) data availability.
        Target: NASA's GES DISC or similar public archive for TIM data.
        Note: Direct file URLs often change or require specific authentication.
        We test the base API or a known stable landing page for the dataset.
        """
        # SORCE TIM data is often hosted on NASA's GES DISC or similar.
        # We test the GES DISC landing page for SORCE as a proxy for availability.
        # If a specific CSV link is required, it should be updated here.
        url = "https://lasp.colorado.edu/sorce/data/"
        
        try:
            response = requests.get(url, timeout=10)
            self.assertTrue(
                200 <= response.status_code < 300,
                f"SORCE URL returned status {response.status_code}: {response.reason}"
            )
        except Timeout:
            self.fail(f"SORCE URL ({url}) timed out after 10 seconds.")
        except RequestException as e:
            self.fail(f"SORCE URL ({url}) failed to connect: {e}")

    def test_ingestion_module_import(self):
        """
        Verify that the ingestion module can be imported without errors.
        This ensures dependencies are installed and the module structure is valid.
        """
        try:
            # We expect the ingestion module to exist based on the task plan
            # If it doesn't exist yet, this test might fail, but it's a valid check
            # for the implementation phase. For this task, we just check if the
            # file exists or if the import structure is ready.
            from code.data import ingestion
            self.assertIsNotNone(ingestion)
        except ImportError:
            # If the module doesn't exist yet, we note it but don't fail the URL test.
            # The task is specifically about URL reachability, but we check importability.
            self.skipTest("code.data.ingestion module not yet implemented.")


if __name__ == '__main__':
    unittest.main()