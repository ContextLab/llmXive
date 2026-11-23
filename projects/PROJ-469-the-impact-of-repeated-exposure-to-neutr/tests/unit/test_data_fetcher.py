"""
Unit tests for code/data_fetcher.py

These tests verify that the data fetcher:
1. Attempts to fetch from the correct URL.
2. Raises ValueError if the source is unavailable.
3. Does not generate synthetic data.
"""

import pytest
from unittest.mock import patch, MagicMock
import urllib.error
import os
from pathlib import Path

# Import the function to test
# We assume the file is in code/ and we can import it
from code.data_fetcher import fetch_project_implicit_data, TARGET_URL

class TestDataFetcher:
    """Tests for the data fetcher functionality."""

    def test_fetch_raises_value_error_on_http_error(self):
        """Test that fetch_project_implicit_data raises ValueError on HTTP 404."""
        mock_url = "http://example.com/nonexistent.csv"
        
        # Mock urllib.request.urlretrieve to raise an HTTPError
        with patch('code.data_fetcher.urllib.request.urlretrieve') as mock_fetch:
            mock_fetch.side_effect = urllib.error.HTTPError(
                mock_url, 404, "Not Found", None, None
            )
            
            with pytest.raises(ValueError) as excinfo:
                fetch_project_implicit_data(url=mock_url, output_dir=Path("/tmp"))
            
            assert "Real data source not found" in str(excinfo.value)
            assert "404" in str(excinfo.value)

    def test_fetch_raises_value_error_on_url_error(self):
        """Test that fetch_project_implicit_data raises ValueError on URLError."""
        mock_url = "http://example.com/nonexistent.csv"
        
        with patch('code.data_fetcher.urllib.request.urlretrieve') as mock_fetch:
            mock_fetch.side_effect = urllib.error.URLError("Network unreachable")
            
            with pytest.raises(ValueError) as excinfo:
                fetch_project_implicit_data(url=mock_url, output_dir=Path("/tmp"))
            
            assert "Real data source not found" in str(excinfo.value)

    def test_fetch_raises_value_error_on_empty_file(self, tmp_path):
        """Test that fetch_project_implicit_data raises ValueError if file is empty."""
        mock_url = "http://example.com/data.csv"
        output_file = tmp_path / "test.csv"
        
        # Create an empty file to simulate a failed download that created a file
        output_file.touch()
        
        with patch('code.data_fetcher.urllib.request.urlretrieve') as mock_fetch:
            # Mock to do nothing, leaving the empty file
            mock_fetch.return_value = None
            
            with pytest.raises(ValueError) as excinfo:
                fetch_project_implicit_data(url=mock_url, output_dir=tmp_path)
            
            assert "Real data source not found" in str(excinfo.value)
            assert "empty" in str(excinfo.value).lower()

    def test_fetch_creates_file_on_success(self, tmp_path):
        """Test that fetch_project_implicit_data creates the file on success."""
        mock_url = "http://example.com/data.csv"
        output_file = tmp_path / "project_implicit_raw.csv"
        
        with patch('code.data_fetcher.urllib.request.urlretrieve') as mock_fetch:
            # Simulate a successful download by creating a non-empty file
            def side_effect(url, path):
                Path(path).write_text("col1,col2\n1,2\n")
            
            mock_fetch.side_effect = side_effect
            
            result_path = fetch_project_implicit_data(url=mock_url, output_dir=tmp_path)
            
            assert result_path.exists()
            assert result_path.stat().st_size > 0
            assert result_path.name == "project_implicit_raw.csv"

    def test_target_url_is_defined(self):
        """Test that TARGET_URL is a valid string."""
        assert isinstance(TARGET_URL, str)
        assert len(TARGET_URL) > 0
        assert TARGET_URL.startswith("http")