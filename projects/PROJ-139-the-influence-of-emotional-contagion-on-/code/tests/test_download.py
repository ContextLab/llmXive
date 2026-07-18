"""
code/tests/test_download.py

Unit tests for the data download pipeline.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import json
import tempfile

from code.data.download import (
    fetch_from_pushshift,
    fetch_from_reddit_api,
    fetch_from_huggingface,
    download_data
)

class TestPushshiftFetch:
    @patch('code.data.download.requests.get')
    def test_fetch_success(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "author": "user1", "subreddit": "test", "selftext": "Hello", "created_utc": 123456, "num_comments": 5},
                {"id": "2", "author": "user2", "subreddit": "test", "selftext": "World", "created_utc": 123457, "num_comments": 2}
            ]
        }
        mock_get.return_value = mock_response

        df, source = fetch_from_pushshift(["test"], limit=10)
        
        assert df is not None
        assert source == "pushshift"
        assert len(df) == 2
        assert "id" in df.columns
        assert "author" in df.columns

    @patch('code.data.download.requests.get')
    def test_fetch_failure(self, mock_get):
        # Mock network error
        mock_get.side_effect = Exception("Network Error")

        df, source = fetch_from_pushshift(["test"], limit=10)
        
        assert df is None
        assert source == "pushshift_unreachable"

class TestRedditAPIFetch:
    @patch('code.data.download.get_config')
    @patch('code.data.download.requests.post')
    @patch('code.data.download.requests.get')
    def test_fetch_success(self, mock_get, mock_post, mock_config):
        # Setup config mock
        mock_config.return_value.api_keys.reddit_client_id = "client_id"
        mock_config.return_value.api_keys.reddit_client_secret = "secret"

        # Mock token response
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "fake_token"}
        mock_post.return_value = mock_token_resp

        # Mock data response
        mock_data_resp = MagicMock()
        mock_data_resp.json.return_value = {
            "data": {
                "children": [
                    {"data": {"id": "1", "author": "user1", "subreddit": "test", "selftext": "Hello", "created_utc": 123456, "num_comments": 5}}
                ]
            }
        }
        mock_get.return_value = mock_data_resp

        df, source = fetch_from_reddit_api(["test"], limit=10)

        assert df is not None
        assert source == "reddit_api"
        assert len(df) == 1

    @patch('code.data.download.get_config')
    def test_fetch_missing_creds(self, mock_config):
        mock_config.return_value.api_keys.reddit_client_id = None

        df, source = fetch_from_reddit_api(["test"], limit=10)

        assert df is None
        assert source == "reddit_api_missing_creds"

class TestDownloadData:
    @patch('code.data.download.fetch_from_pushshift')
    def test_download_success_pushshift(self, mock_push):
        mock_push.return_value = (
            pd.DataFrame([{"id": "1", "author": "u1", "subreddit": "s1", "selftext": "t", "created_utc": 1, "num_comments": 0}]),
            "pushshift"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "data.csv")
            result = download_data(["s1"], output_path, limit=10)
            
            assert result["success"] is True
            assert result["source"] == "pushshift"
            assert os.path.exists(output_path)
            assert result["record_count"] == 1

    @patch('code.data.download.fetch_from_pushshift')
    @patch('code.data.download.fetch_from_reddit_api')
    def test_download_fallback_to_reddit(self, mock_reddit, mock_push):
        # Pushshift fails
        mock_push.return_value = (None, "pushshift_unreachable")
        # Reddit succeeds
        mock_reddit.return_value = (
            pd.DataFrame([{"id": "2", "author": "u2", "subreddit": "s1", "selftext": "t2", "created_utc": 2, "num_comments": 1}]),
            "reddit_api"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "data.csv")
            result = download_data(["s1"], output_path, limit=10)
            
            assert result["success"] is True
            assert result["source"] == "reddit_api"
            assert result["record_count"] == 1

    @patch('code.data.download.fetch_from_pushshift')
    @patch('code.data.download.fetch_from_reddit_api')
    @patch('code.data.download.fetch_from_huggingface')
    def test_download_fallback_to_huggingface(self, mock_hf, mock_reddit, mock_push):
        mock_push.return_value = (None, "pushshift_unreachable")
        mock_reddit.return_value = (None, "reddit_api_failed")
        mock_hf.return_value = (
            pd.DataFrame([{"id": "3", "author": "u3", "subreddit": "s1", "selftext": "t3", "created_utc": 3, "num_comments": 2}]),
            "huggingface"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "data.csv")
            result = download_data(["s1"], output_path, limit=10)
            
            assert result["success"] is True
            assert result["source"] == "huggingface"
            assert result["record_count"] == 1

    @patch('code.data.download.fetch_from_pushshift')
    @patch('code.data.download.fetch_from_reddit_api')
    @patch('code.data.download.fetch_from_huggingface')
    def test_download_all_fail(self, mock_hf, mock_reddit, mock_push):
        mock_push.return_value = (None, "pushshift_unreachable")
        mock_reddit.return_value = (None, "reddit_api_failed")
        mock_hf.return_value = (None, "huggingface_failed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "data.csv")
            result = download_data(["s1"], output_path, limit=10)
            
            assert result["success"] is False
            assert result["error"] == "All data sources failed."
