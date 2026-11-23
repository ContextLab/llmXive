"""
Unit tests for generate_target_list.py
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.generate_target_list import build_query, fetch_repo_metadata
from config import TARGET_MIN_STARS

class TestGenerateTargetList(unittest.TestCase):

    def test_build_query_uses_config(self):
        """Test that build_query uses TARGET_MIN_STARS from config."""
        query = build_query(TARGET_MIN_STARS)
        self.assertIn(f"stars:>={TARGET_MIN_STARS}", query)
        self.assertIn("is:public", query)

    @patch('data.generate_target_list.requests.get')
    def test_fetch_repo_metadata_success(self, mock_get):
        """Test successful fetch and CSV creation."""
        # Mock response for page 1
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "html_url": "https://github.com/test/repo1",
                    "language": "Python",
                    "stargazers_count": 2000,
                    "created_at": "2020-01-01T00:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response

        output_path = Path("data/raw/test_target_list.csv")
        try:
            fetch_repo_metadata("stars:>=1000 is:public", output_path)
            
            # Check file exists
            self.assertTrue(output_path.exists())
            
            # Check content
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]['url'], "https://github.com/test/repo1")
            self.assertEqual(df.iloc[0]['primary_language'], "Python")
            self.assertEqual(df.iloc[0]['stars'], 2000)
            self.assertIn('age', df.columns)
        finally:
            if output_path.exists():
                output_path.unlink()

    @patch('data.generate_target_list.requests.get')
    def test_fetch_repo_metadata_403_abort(self, mock_get):
        """Test that 403 error causes abort."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            fetch_repo_metadata("stars:>=1000 is:public", Path("data/raw/test.csv"))
        
        self.assertIn("403 Forbidden", str(context.exception))

    @patch('data.generate_target_list.requests.get')
    def test_fetch_repo_metadata_429_backoff(self, mock_get):
        """Test that 429 triggers retry logic."""
        # First two calls return 429, third returns 200
        mock_429 = MagicMock()
        mock_429.status_code = 429
        
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"items": []}
        
        mock_get.side_effect = [mock_429, mock_429, mock_200]

        output_path = Path("data/raw/test.csv")
        try:
            fetch_repo_metadata("stars:>=1000 is:public", output_path)
            # Should succeed after retries
            self.assertTrue(output_path.exists())
        finally:
            if output_path.exists():
                output_path.unlink()

if __name__ == "__main__":
    unittest.main()
