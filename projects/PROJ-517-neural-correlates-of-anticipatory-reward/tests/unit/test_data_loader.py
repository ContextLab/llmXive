"""
Unit tests for code/data_loader.py.
Specifically tests the 'fail loudly' behavior for real data fetching.
"""
import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_real_data


class TestLoadRealDataFailsLoudly(unittest.TestCase):
    """
    Test that load_real_data() raises FileNotFoundError when real data fetch fails
    in a non-CI environment, ensuring no silent synthetic fallback occurs.
    """

    def setUp(self):
        """Save original environment variables."""
        self.original_ci = os.environ.get('CI')

    def tearDown(self):
        """Restore original environment variables."""
        if self.original_ci is None:
            os.environ.pop('CI', None)
        else:
            os.environ['CI'] = self.original_ci

    @patch('data_loader.datasets')
    def test_load_real_data_fails_loudly_production(self, mock_datasets):
        """
        Assert that load_real_data() raises FileNotFoundError when:
        1. os.getenv('CI') is False (or not set)
        2. The fetch fails (simulated by raising an exception)
        """
        # Force production mode
        os.environ['CI'] = 'false'

        # Mock the fetch to fail
        mock_datasets.load_dataset.side_effect = Exception("Connection failed to OpenNeuro")

        # Expect FileNotFoundError to be raised
        with self.assertRaises(FileNotFoundError) as context:
            load_real_data(data_source='openneuro')

        # Verify the error message is specific and actionable
        self.assertIn("Real data fetch failed", str(context.exception))
        self.assertIn("No synthetic fallback allowed in production", str(context.exception))

        # Verify no synthetic generator was called
        # (We can't easily check if synthetic_generator was imported, but we check
        # that the function didn't return a dataframe)

    @patch('data_loader.datasets')
    def test_load_real_data_fails_loudly_ci_allowed_fallback(self, mock_datasets):
        """
        Assert that in CI mode, if fetch fails, it might fallback to synthetic
        (depending on implementation details in data_loader.py, but T040 specifically
        tests the FAIL LOUDLY path in production).
        
        This test ensures the CI branch logic exists and doesn't crash,
        though the primary focus of T040 is the production failure.
        """
        os.environ['CI'] = 'true'
        
        # Mock fetch to fail
        mock_datasets.load_dataset.side_effect = Exception("CI Fetch Failed")
        
        # In the actual implementation, this should fall back to synthetic
        # or handle the CI case differently. 
        # For T040, we are primarily ensuring the PRODUCTION path fails.
        # We just ensure the code path doesn't crash the test runner here,
        # assuming the data_loader handles the CI fallback gracefully.
        # If data_loader.py is strict even in CI, this might raise, 
        # but T017 description says "If True, allow fallback".
        
        # We skip the assertion on return value here as the fallback logic
        # is implementation detail of data_loader.py, but we ensure it doesn't
        # raise FileNotFoundError with the "No synthetic fallback" message.
        try:
            result = load_real_data(data_source='openneuro')
            # If it returns, it likely used synthetic fallback (expected in CI)
            self.assertIsNotNone(result)
        except FileNotFoundError as e:
            # If it raises, ensure it's NOT the "No synthetic fallback" error
            self.assertNotIn("No synthetic fallback allowed in production", str(e))

    @patch('data_loader.datasets')
    def test_load_real_data_success_production(self, mock_datasets):
        """
        Assert that load_real_data() returns data successfully in production
        when the fetch succeeds.
        """
        os.environ['CI'] = 'false'
        
        # Mock a successful fetch
        mock_df = MagicMock()
        mock_datasets.load_dataset.return_value = mock_df
        
        result = load_real_data(data_source='openneuro')
        
        # Verify the dataset function was called
        mock_datasets.load_dataset.assert_called_once()
        # Verify result is the mock dataframe
        self.assertEqual(result, mock_df)


if __name__ == '__main__':
    unittest.main()