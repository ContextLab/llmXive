"""
Tests to verify the strict "fail-loud" policy in download.py.
Ensures that no synthetic data is generated and that RuntimeError is raised on failure.
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.download import download_data, fetch_from_pushshift, fetch_from_reddit_api, fetch_from_internet_archive
from config.settings import Config, APIKeys, DatasetPaths

class TestFailLoudPolicy(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directories and mock config."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.processed_dir = os.path.join(self.temp_dir, "processed")
        self.state_dir = os.path.join(self.temp_dir, "state")
        os.makedirs(self.raw_dir)
        os.makedirs(self.processed_dir)
        os.makedirs(self.state_dir)
        
        # Mock config
        self.mock_config = Config(
            api_keys=APIKeys(
                pushshift_api_key="fake_key",
                reddit_client_id="fake_id",
                reddit_client_secret="fake_secret",
                reddit_user_agent="test-bot"
            ),
            paths=DatasetPaths(
                raw_data=self.raw_dir,
                processed_data=self.processed_dir,
                state=self.state_dir
            )
        )
        
        # Patch get_config to return our mock
        self.config_patcher = patch('data.download.get_config', return_value=self.mock_config)
        self.config_patcher.start()

    def tearDown(self):
        """Clean up temporary files."""
        self.config_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('data.download.requests.get')
    def test_pushshift_failure_raises_error(self, mock_get):
        """Test that Pushshift failure leads to RuntimeError when all sources fail."""
        # Mock Pushshift to fail
        mock_get.return_value.status_code = 404
        
        # Mock Reddit API to fail
        with patch('data.download.fetch_from_reddit_api', return_value=(None, False)):
            # Mock Internet Archive to fail
            with patch('data.download.fetch_from_internet_archive', return_value=(None, False)):
                with self.assertRaises(RuntimeError) as context:
                    download_data(["test_subreddit"], os.path.join(self.raw_dir, "test.jsonl"))
                
                self.assertIn("CRITICAL FAILURE", str(context.exception))
                self.assertIn("test_subreddit", str(context.exception))

    @patch('data.download.requests.get')
    def test_successful_pushshift_does_not_raise(self, mock_get):
        """Test that successful Pushshift fetch does not raise error."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "subreddit": "test", "created_utc": 123, "author": "u1", "title": "t", "selftext": "s", "link_id": "l", "parent_id": "p"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Should not raise
        try:
            download_data(["test_subreddit"], os.path.join(self.raw_dir, "test.jsonl"))
        except RuntimeError:
            self.fail("download_data raised RuntimeError unexpectedly")
        
        # Verify file was created
        output_file = os.path.join(self.raw_dir, "test.jsonl")
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("1", content)

    def test_no_synthetic_fallback(self):
        """
        Verify that the code does NOT contain fallback logic to generate synthetic data.
        This is a code inspection test.
        """
        import inspect
        source = inspect.getsource(download_data)
        
        # Check for forbidden patterns
        forbidden_patterns = [
            "generate_synthetic",
            "mock_data",
            "np.random",
            "random.sample",
            "synthetic_data",
            "fake_data"
        ]
        
        for pattern in forbidden_patterns:
            # Ensure pattern is not present in the main logic (excluding comments/tests)
            # We check if the pattern appears in the actual logic flow
            if pattern in source:
                # If found, ensure it's not in a fallback branch
                # For this strict test, we assume any presence is a violation unless it's clearly a comment
                lines = source.split('\n')
                for line in lines:
                    if pattern in line and not line.strip().startswith('#'):
                        self.fail(f"Found forbidden synthetic pattern '{pattern}' in code: {line.strip()}")

if __name__ == '__main__':
    unittest.main()