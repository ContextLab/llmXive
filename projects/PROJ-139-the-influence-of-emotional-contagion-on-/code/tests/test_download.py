"""
Unit tests for data download module.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from code.data.download import (
    fetch_from_pushshift,
    fetch_from_reddit_api,
    fetch_from_huggingface,
    download_data
)


class TestPushshiftFetch:
    """Tests for Pushshift API fetch function."""

    @patch('code.data.download.requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch from Pushshift."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "test1",
                    "title": "Test Post",
                    "author": "test_user",
                    "selftext": "Test content",
                    "created_utc": 1234567890,
                    "num_comments": 5,
                    "subreddit": "AskScience",
                    "url": "http://test.com"
                }
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_from_pushshift(["AskScience"], limit=10)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["id"] == "test1"
        assert result.iloc[0]["origin_type"] == "pushshift"

    @patch('code.data.download.requests.get')
    def test_fetch_empty_response(self, mock_get):
        """Test fetch with empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        result = fetch_from_pushshift(["AskScience"], limit=10)

        assert result is None

    @patch('code.data.download.requests.get')
    def test_fetch_request_exception(self, mock_get):
        """Test fetch with network error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = fetch_from_pushshift(["AskScience"], limit=10)

        assert result is None


class TestRedditAPIFetch:
    """Tests for Reddit Official API fetch function."""

    @patch.dict(os.environ, {
        "REDDIT_CLIENT_ID": "test_client_id",
        "REDDIT_CLIENT_SECRET": "test_client_secret",
        "REDDIT_USER_AGENT": "test_agent"
    })
    @patch('code.data.download.requests.post')
    @patch('code.data.download.requests.get')
    def test_fetch_success(self, mock_get, mock_post):
        """Test successful fetch from Reddit API."""
        # Mock token request
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake_token"}
        mock_post.return_value = mock_token_response

        # Mock posts request
        mock_posts_response = MagicMock()
        mock_posts_response.status_code = 200
        mock_posts_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "reddit1",
                            "title": "Reddit Post",
                            "author": "reddit_user",
                            "selftext": "Reddit content",
                            "created_utc": 1234567890,
                            "num_comments": 10,
                            "subreddit": "AskScience",
                            "url": "http://reddit.com"
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_posts_response

        result = fetch_from_reddit_api(["AskScience"], limit=10)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["id"] == "reddit1"
        assert result.iloc[0]["origin_type"] == "reddit_api"

    @patch.dict(os.environ, {}, clear=True)
    def test_fetch_missing_credentials(self):
        """Test fetch without credentials."""
        result = fetch_from_reddit_api(["AskScience"], limit=10)
        assert result is None


class TestDownloadData:
    """Tests for main download function."""

    @patch('code.data.download.fetch_from_pushshift')
    def test_download_uses_pushshift_first(self, mock_pushshift, tmp_path):
        """Test that download_data tries Pushshift first."""
        mock_df = pd.DataFrame([{"id": "test", "origin_type": "pushshift"}])
        mock_pushshift.return_value = mock_df

        output_path = tmp_path / "test.csv"
        result = download_data(["AskScience"], limit=10, output_path=output_path)

        assert mock_pushshift.called
        assert result.equals(mock_df)
        assert output_path.exists()

    @patch('code.data.download.fetch_from_pushshift')
    @patch('code.data.download.fetch_from_reddit_api')
    def test_download_fallback_to_reddit(self, mock_reddit, mock_pushshift, tmp_path):
        """Test that download_data falls back to Reddit API when Pushshift fails."""
        mock_pushshift.return_value = None
        mock_reddit_df = pd.DataFrame([{"id": "test", "origin_type": "reddit_api"}])
        mock_reddit.return_value = mock_reddit_df

        output_path = tmp_path / "test.csv"
        result = download_data(["AskScience"], limit=10, output_path=output_path)

        assert mock_pushshift.called
        assert mock_reddit.called
        assert result.equals(mock_reddit_df)
        assert result.iloc[0]["origin_type"] == "reddit_api"

    @patch('code.data.download.fetch_from_pushshift')
    @patch('code.data.download.fetch_from_reddit_api')
    @patch('code.data.download.fetch_from_huggingface')
    def test_download_fallback_to_huggingface(self, mock_hf, mock_reddit, mock_pushshift, tmp_path):
        """Test that download_data falls back to HuggingFace when others fail."""
        mock_pushshift.return_value = None
        mock_reddit.return_value = None
        mock_hf_df = pd.DataFrame([{"id": "test", "origin_type": "huggingface"}])
        mock_hf.return_value = mock_hf_df

        output_path = tmp_path / "test.csv"
        result = download_data(["AskScience"], limit=10, output_path=output_path)

        assert mock_pushshift.called
        assert mock_reddit.called
        assert mock_hf.called
        assert result.equals(mock_hf_df)
        assert result.iloc[0]["origin_type"] == "huggingface"

    @patch('code.data.download.fetch_from_pushshift')
    @patch('code.data.download.fetch_from_reddit_api')
    @patch('code.data.download.fetch_from_huggingface')
    def test_download_all_sources_fail(self, mock_hf, mock_reddit, mock_pushshift):
        """Test that download_data raises error when all sources fail."""
        mock_pushshift.return_value = None
        mock_reddit.return_value = None
        mock_hf.return_value = None

        with pytest.raises(RuntimeError, match="All data sources.*failed"):
            download_data(["AskScience"], limit=10)
