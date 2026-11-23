"""
Integration tests for the data ingestion module, specifically focusing on the
'Fail Loudly' constraint for real data fetching.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data_ingestion import download_datasets
from config import get_config_dict

class TestRealDataFetchFailsLoudly(unittest.TestCase):
    """
    Tests to verify that download_datasets raises an exception when real data
    sources are unreachable and does NOT fallback to synthetic data.
    """

    @patch('data_ingestion.requests.get')
    @patch('data_ingestion.datasets.load_dataset')
    def test_download_datasets_raises_on_network_failure(self, mock_load_dataset, mock_requests_get):
        """
        Asserts that download_datasets raises a ConnectionError when the network
        request fails, and does not fallback to synthetic data generation.
        """
        # Mock the network request to fail
        mock_requests_get.side_effect = Exception("Network failure: Unable to connect to MSD source")
        
        # Mock config to ensure we are in Final Mode (USE_MOCK_DATA = False)
        # We patch the config dict returned by get_config_dict
        with patch('data_ingestion.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MSD_URL': 'https://fake-msd-url.com/data',
                'AMT_URL': 'https://fake-amt-url.com/data',
                'USE_MOCK_DATA': False,
                'PROJECT_ROOT': '/tmp/test_project'
            }
            
            # Ensure the function raises an exception
            with self.assertRaises(Exception) as context:
                download_datasets()
            
            # Verify the exception message indicates a connection/fetch failure
            self.assertIn("Network failure", str(context.exception))

    @patch('data_ingestion.datasets.load_dataset')
    def test_download_datasets_raises_on_dataset_fetch_failure(self, mock_load_dataset):
        """
        Asserts that download_datasets raises an exception when the HuggingFace
        dataset fetch fails, and does not fallback to synthetic data.
        """
        # Mock the dataset loading to fail
        mock_load_dataset.side_effect = ConnectionError("Failed to connect to HuggingFace Hub")

        with patch('data_ingestion.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MSD_URL': 'hf://brian/MSD',
                'AMT_URL': 'hf://validated-AMT-source',
                'USE_MOCK_DATA': False,
                'PROJECT_ROOT': '/tmp/test_project'
            }

            # Ensure the function raises an exception
            with self.assertRaises(ConnectionError):
                download_datasets()

    @patch('data_ingestion.requests.get')
    def test_download_datasets_no_synthetic_fallback(self, mock_requests_get):
        """
        Explicitly verifies that NO synthetic data is generated when the real
        source is unreachable. This test passes if the function raises
        an exception before any 'generate_synthetic' or 'mock' logic could run.
        """
        # Mock network failure
        mock_requests_get.side_effect = ConnectionError("Connection refused")

        with patch('data_ingestion.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MSD_URL': 'https://fake-url.com',
                'AMT_URL': 'https://fake-url.com',
                'USE_MOCK_DATA': False,
                'PROJECT_ROOT': '/tmp/test_project'
            }

            # We expect an exception, NOT a successful return with fake data
            with self.assertRaises(ConnectionError):
                result = download_datasets()
                # If we get here, the function returned without raising,
                # which means it might have fallen back to synthetic data (if logic existed)
                # or simply failed silently. We assert this path should not be taken.
                self.fail("download_datasets should have raised an exception and not returned a result.")

    @patch('data_ingestion.datasets.load_dataset')
    @patch('data_ingestion.requests.get')
    def test_download_datasets_success_in_prototype_mode(self, mock_requests_get, mock_load_dataset):
        """
        Verifies that in Prototype Mode (USE_MOCK_DATA=True), the function does
        NOT raise an exception when real sources are missing, but proceeds to
        load local mock data (or skips real fetch).
        """
        # Simulate that real fetch would fail, but we are in prototype mode
        mock_requests_get.side_effect = ConnectionError("Real source down")
        
        # We don't mock load_dataset here because in prototype mode, 
        # the logic should bypass the real fetch entirely or handle it gracefully.
        # For this test, we assume the logic checks USE_MOCK_DATA first.
        
        with patch('data_ingestion.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MSD_URL': 'https://fake-url.com',
                'AMT_URL': 'https://fake-url.com',
                'USE_MOCK_DATA': True,
                'PROJECT_ROOT': '/tmp/test_project'
            }
            
            # In prototype mode, if the code is implemented correctly, 
            # it should not attempt the real fetch or should handle the missing file gracefully.
            # Since we are mocking the fetch to fail, we need to ensure the code 
            # checks the flag BEFORE attempting the fetch.
            # If the code is correct, it will not call requests.get or load_dataset 
            # when USE_MOCK_DATA is True and local files are expected.
            
            # To simulate success in prototype mode without real files, 
            # we assume the function has a path for local mock data that doesn't 
            # require network access. If the implementation relies on network 
            # even in prototype mode, this test would need adjustment to mock 
            # the local file existence.
            # For now, we test the logic path: if USE_MOCK_DATA is True, 
            # the function should not raise ConnectionError.
            
            # Since we can't easily simulate "local file exists" without file I/O,
            # we rely on the fact that the function should return early or 
            # catch the error if it tries to fetch.
            # If the implementation is:
            # if USE_MOCK_DATA: return load_local_mock()
            # else: try real fetch -> raise
            # Then this test passes if no exception is raised.
            
            # However, since we are mocking the fetch to raise, we must ensure
            # the code does not reach the fetch line.
            # We will assume the implementation checks USE_MOCK_DATA first.
            # If the implementation is flawed and tries to fetch regardless,
            # this test will fail, indicating a bug.
            
            try:
                download_datasets()
            except ConnectionError:
                self.fail("In Prototype Mode, download_datasets should not raise ConnectionError.")

if __name__ == '__main__':
    unittest.main()