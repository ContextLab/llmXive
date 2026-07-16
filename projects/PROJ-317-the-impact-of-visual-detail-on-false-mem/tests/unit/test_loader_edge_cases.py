"""
Unit tests for edge cases in the data loader module:
- Missing metadata handling
- Fetch failure handling (no silent fallback)
"""
import logging
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.loader import load_image_metadata, process_image_with_error_handling
from config import get_stimuli_metadata_dir


class TestLoaderEdgeCases(unittest.TestCase):
    """Test edge cases for data loading: missing metadata and fetch failures."""

    def setUp(self):
        """Set up test fixtures."""
        self.metadata_dir = get_stimuli_metadata_dir()
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        """Clean up test artifacts."""
        # Clean up any test metadata files
        test_meta = self.metadata_dir / "test_missing_meta.yaml"
        if test_meta.exists():
            test_meta.unlink()

    def test_missing_metadata_raises_error(self):
        """
        Test that when metadata file is missing, the loader:
        1. Raises a FileNotFoundError (or appropriate exception)
        2. Does NOT return a mock/synthetic object
        """
        non_existent_id = "non_existent_image_12345"
        metadata_path = self.metadata_dir / f"{non_existent_id}.yaml"
        
        # Ensure file does not exist
        if metadata_path.exists():
            metadata_path.unlink()
        
        # Verify that load_image_metadata raises an error
        # The requirement is to FAIL LOUDLY, not fall back to synthetic
        with self.assertRaises(FileNotFoundError):
            load_image_metadata(non_existent_id)

    def test_fetch_failure_raises_error(self):
        """
        Test that when fetching a real dataset image fails, the loader:
        1. Raises an exception (TimeoutError, HTTPError, etc.)
        2. Does NOT silently generate synthetic data or mock objects
        """
        # Mock the fetch function to simulate a network failure
        with patch('data.loader.fetch_real_dataset_image') as mock_fetch:
            mock_fetch.side_effect = Exception("Network unreachable: Connection refused")
            
            # We expect the process_image_with_error_handling to propagate the error
            # or handle it by raising, not by returning a mock.
            # Based on the requirement "FAIL LOUDLY", we expect an exception.
            with self.assertRaises(Exception):
                process_image_with_error_handling(
                    image_id="test_fetch_fail",
                    target_dir=Path("/tmp/test_fetch"),
                    fetch_func=mock_fetch
                )

    def test_process_image_with_error_handling_skips_and_logs(self):
        """
        Test the error handling wrapper that should:
        1. Catch processing errors
        2. Log them
        3. Return a failure status (not a mock image)
        """
        # We test the logic that ensures we don't return fake data.
        # If the fetch fails, we expect the function to either raise
        # or return a specific error structure, but NOT a valid Image object
        # with synthetic data.
        
        def failing_fetcher(image_id):
            raise ConnectionError("Simulated network failure")
        
        with patch('data.loader.fetch_real_dataset_image', side_effect=failing_fetcher):
            with self.assertRaises(ConnectionError):
                # The function should propagate the error, not swallow it
                process_image_with_error_handling(
                    image_id="fail_test",
                    target_dir=Path("/tmp"),
                    fetch_func=failing_fetcher
                )


if __name__ == "__main__":
    unittest.main()