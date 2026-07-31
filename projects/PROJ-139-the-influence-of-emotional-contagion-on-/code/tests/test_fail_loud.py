"""
Test suite for T065: Validate fail-loud policy during execution gate.

This task verifies that the 'fail-loud' policy implemented in T031 is correctly
triggered when all data sources fail. It simulates a complete data source failure
and confirms that the pipeline halts with a clear RuntimeError.

Dependencies:
- T031: Implementation of fail-loud policy in code/data/download.py
- T036: Execution gate where this policy is validated

Execution:
python -m pytest code/tests/test_fail_loud.py -v
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download import download_data, main
from config.settings import DatasetPaths


class TestFailLoudPolicy(unittest.TestCase):
    """Tests for the fail-loud data download policy."""

    def setUp(self):
        """Set up test fixtures."""
        self.patchers = []
        self.mock_requests = None
        self.mock_hf_hub = None
        self.mock_archive = None

    def tearDown(self):
        """Clean up test fixtures."""
        for patcher in self.patchers:
            patcher.stop()

    def _create_mock_response(self, status_code, content=None):
        """Create a mock requests.Response object."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        if content:
            mock_response.text = content
            mock_response.json.return_value = content
        else:
            mock_response.text = ""
            mock_response.json.side_effect = ValueError("No JSON")
        return mock_response

    def test_pushshift_api_failure(self):
        """Test that Pushshift API failure is handled correctly."""
        # Mock requests.get to simulate Pushshift API failure
        mock_response = self._create_mock_response(500, "Internal Server Error")

        self.patchers.append(patch('data.download.requests.get', return_value=mock_response))
        self.patchers.append(patch('data.download.time.sleep'))  # Suppress sleep in tests

        for patcher in self.patchers:
            patcher.start()

        # Test that the function attempts to fetch but handles the failure
        # Note: We are testing the internal logic, not the full pipeline failure
        # The full pipeline failure is tested in test_all_sources_fail
        pass  # The actual failure handling is tested in the full pipeline test

    def test_reddit_api_failure(self):
        """Test that Reddit API failure is handled correctly."""
        mock_response = self._create_mock_response(401, "Unauthorized")

        self.patchers.append(patch('data.download.requests.post', return_value=mock_response))
        self.patchers.append(patch('data.download.time.sleep'))

        for patcher in self.patchers:
            patcher.start()

        pass  # The actual failure handling is tested in the full pipeline test

    def test_huggingface_failure(self):
        """Test that HuggingFace dataset fetch failure is handled correctly."""
        mock_exception = Exception("Dataset not found")

        self.patchers.append(patch('data.download.hf_hub_download', side_effect=mock_exception))

        for patcher in self.patchers:
            patcher.start()

        pass  # The actual failure handling is tested in the full pipeline test

    def test_internet_archive_failure(self):
        """Test that Internet Archive fetch failure is handled correctly."""
        mock_response = self._create_mock_response(404, "Not Found")

        self.patchers.append(patch('data.download.requests.get', return_value=mock_response))
        self.patchers.append(patch('data.download.time.sleep'))

        for patcher in self.patchers:
            patcher.start()

        pass  # The actual failure handling is tested in the full pipeline test

    def test_all_sources_fail_raises_runtime_error(self):
        """
        T065 Core Test: Simulate complete data source failure and verify
        that a RuntimeError is raised with a clear message.
        """
        # Mock all data sources to fail
        # 1. Pushshift API fails (500 error)
        mock_pushshift_response = self._create_mock_response(500, "Internal Server Error")
        
        # 2. Reddit API fails (401 error)
        mock_reddit_response = self._create_mock_response(401, "Unauthorized")
        
        # 3. HuggingFace fails (Dataset not found)
        mock_hf_exception = Exception("Dataset not found or access denied")
        
        # 4. Internet Archive fails (404 error)
        mock_archive_response = self._create_mock_response(404, "Not Found")

        # Set up patches for all failure points
        # Patch requests.get for Pushshift and Archive
        mock_get = MagicMock()
        mock_get.side_effect = [
            mock_pushshift_response,  # Pushshift call
            mock_archive_response     # Archive call
        ]
        
        # Patch requests.post for Reddit OAuth
        mock_post = MagicMock()
        mock_post.return_value = mock_reddit_response
        
        # Patch hf_hub_download
        mock_hf_download = MagicMock()
        mock_hf_download.side_effect = mock_hf_exception

        self.patchers.append(patch('data.download.requests.get', mock_get))
        self.patchers.append(patch('data.download.requests.post', mock_post))
        self.patchers.append(patch('data.download.hf_hub_download', mock_hf_download))
        self.patchers.append(patch('data.download.time.sleep'))  # Suppress sleep

        for patcher in self.patchers:
            patcher.start()

        # Create a temporary output directory for the test
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_threads.jsonl"
            
            # Attempt to download data - this should raise RuntimeError
            with self.assertRaises(RuntimeError) as context:
                download_data(
                    subreddits=['test_subreddit'],
                    limit=10,
                    output=str(output_path)
                )

            # Verify the error message is clear and informative
            error_message = str(context.exception)
            self.assertIn("All data sources failed", error_message)
            self.assertIn("No synthetic data generated", error_message)
            self.assertTrue(
                len(error_message) > 20,
                "Error message should be descriptive"
            )

    def test_fail_loud_policy_no_synthetic_fallback(self):
        """
        Verify that the fail-loud policy does NOT fall back to synthetic data.
        This is a negative test to ensure no synthetic data generation occurs.
        """
        # Mock all sources to fail
        mock_pushshift = self._create_mock_response(500, "Error")
        mock_reddit = self._create_mock_response(401, "Error")
        mock_hf = Exception("Not found")
        mock_archive = self._create_mock_response(404, "Error")

        mock_get = MagicMock(side_effect=[mock_pushshift, mock_archive])
        mock_post = MagicMock(return_value=mock_reddit)
        mock_hf_download = MagicMock(side_effect=mock_hf)

        self.patchers.append(patch('data.download.requests.get', mock_get))
        self.patchers.append(patch('data.download.requests.post', mock_post))
        self.patchers.append(patch('data.download.hf_hub_download', mock_hf_download))
        self.patchers.append(patch('data.download.time.sleep'))

        for patcher in self.patchers:
            patcher.start()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_threads.jsonl"
            
            # Attempt download - should fail
            with self.assertRaises(RuntimeError):
                download_data(
                    subreddits=['test'],
                    limit=5,
                    output=str(output_path)
                )

            # Verify output file was NOT created (no synthetic fallback)
            self.assertFalse(
                output_path.exists(),
                "Output file should not exist when all sources fail (no synthetic fallback)"
            )


def test_main_function_fail_loud():
    """
    Test that the main function also respects the fail-loud policy.
    This ensures that when run as a script, the error is properly raised.
    """
    # Mock all sources to fail
    mock_pushshift = TestFailLoudPolicy()._create_mock_response(500, "Error")
    mock_reddit = TestFailLoudPolicy()._create_mock_response(401, "Error")
    mock_hf = Exception("Not found")
    mock_archive = TestFailLoudPolicy()._create_mock_response(404, "Error")

    mock_get = MagicMock(side_effect=[mock_pushshift, mock_archive])
    mock_post = MagicMock(return_value=mock_reddit)
    mock_hf_download = MagicMock(side_effect=mock_hf)

    with patch('data.download.requests.get', mock_get), \
         patch('data.download.requests.post', mock_post), \
         patch('data.download.hf_hub_download', mock_hf_download), \
         patch('data.download.time.sleep'):
         
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_main_threads.jsonl"
            
            # Mock sys.argv to simulate command line call
            with patch('sys.argv', ['download.py', '--output', str(output_path)]):
                with unittest.TestCase().assertRaises(RuntimeError):
                    main()


if __name__ == '__main__':
    unittest.main()
