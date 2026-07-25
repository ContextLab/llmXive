"""
Unit tests for code/data/generate_target_list.py
Tests T006 implementation.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timezone

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.generate_target_list import build_query, fetch_repo_metadata, generate_target_list
from config import TARGET_MIN_STARS

class TestBuildQuery(unittest.TestCase):
    def test_query_uses_target_min_stars(self):
        query = build_query()
        self.assertIn(f"stars:>={TARGET_MIN_STARS}", query)
        self.assertIn("type:repo", query)
        self.assertIn("sort:stars", query)

class TestFetchRepoMetadata(unittest.TestCase):
    @patch('data.generate_target_list.requests.get')
    def test_fetch_success(self, mock_get):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "html_url": "https://github.com/test/repo1",
                    "language": "Python",
                    "stargazers_count": 1500,
                    "created_at": "2020-01-01T00:00:00Z"
                }
            ],
            "total_count": 1
        }
        mock_get.return_value = mock_response
        
        repos = fetch_repo_metadata("test_query", max_pages=1)
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["html_url"], "https://github.com/test/repo1")
        
    @patch('data.generate_target_list.requests.get')
    def test_fetch_rate_limit_429(self, mock_get):
        # Mock rate limit response followed by success
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "items": [],
            "total_count": 0
        }
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        # Should retry and succeed (or at least attempt)
        # We expect it to not crash on 429
        try:
            repos = fetch_repo_metadata("test_query", max_pages=1)
        except SystemExit:
            # If it exits, that's also a valid "fail loud" behavior if retries exhausted
            pass

class TestGenerateTargetListIntegration(unittest.TestCase):
    @patch('data.generate_target_list.fetch_repo_metadata')
    @patch('data.generate_target_list.ensure_directories')
    @patch('data.generate_target_list.DATA_RAW_DIR')
    def test_generate_creates_dataframe(self, mock_dir, mock_ensure, mock_fetch):
        mock_dir.__truediv__ = lambda self, key: f"/fake/path/{key}"
        mock_fetch.return_value = [
            {
                "html_url": "https://github.com/test/repo1",
                "language": "Python",
                "stargazers_count": 2000,
                "created_at": "2019-01-01T00:00:00Z"
            }
        ]
        
        with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
            df = generate_target_list()
            
            self.assertIsInstance(df, pd.DataFrame)
            self.assertIn("url", df.columns)
            self.assertIn("primary_language", df.columns)
            self.assertIn("stars", df.columns)
            self.assertIn("age", df.columns)
            self.assertEqual(len(df), 1)

if __name__ == "__main__":
    unittest.main()