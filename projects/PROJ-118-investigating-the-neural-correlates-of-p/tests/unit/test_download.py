"""
Unit tests for the download module.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import tempfile

# Import the module under test
from code.download import fetch_ds003645, retry


class TestRetryDecorator:
    """Tests for the retry decorator logic."""

    def test_retry_success_on_first_try(self):
        """Test that a successful function is called once."""
        @retry(max_attempts=3, backoff=0.1)
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_retry_success_after_failure(self):
        """Test that a function succeeds after a transient failure."""
        call_count = 0

        @retry(max_attempts=3, backoff=0.1)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_exhausts_attempts(self):
        """Test that the decorator raises after max attempts."""
        @retry(max_attempts=2, backoff=0.1)
        def always_fail():
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError):
            always_fail()


class TestFetchDs003645:
    """Tests for the fetch_ds003645 function."""

    def test_fetch_creates_directory(self):
        """Test that the function creates the output directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = os.path.join(tmpdir, "new_subdir")
            assert not os.path.exists(target_dir)
            
            # Mock the download_dataset to avoid actual network call but verify logic
            with patch('code.download.download_dataset') as mock_download:
                mock_download.return_value = target_dir
                result = fetch_ds003645(target_dir)
                
                # Verify directory was created (by the function logic)
                assert os.path.exists(target_dir)
                assert result == target_dir
                mock_download.assert_called_once()

    def test_fetch_returns_valid_path(self):
        """Test that the function returns the path to the downloaded data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_path = os.path.join(tmpdir, "ds003645")
            
            with patch('code.download.download_dataset') as mock_download:
                mock_download.return_value = mock_path
                result = fetch_ds003645(tmpdir)
                
                assert result == mock_path
                assert os.path.exists(result)

    def test_fetch_handles_missing_dataset_error(self):
        """Test handling of ValueError when download returns invalid path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('code.download.download_dataset') as mock_download:
                mock_download.return_value = None
                
                with pytest.raises(ValueError, match="Download reported success"):
                    fetch_ds003645(tmpdir)

    def test_fetch_handles_download_exception(self):
        """Test handling of exceptions raised during download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('code.download.download_dataset') as mock_download:
                mock_download.side_effect = TimeoutError("Network timeout")
                
                with pytest.raises(TimeoutError):
                    fetch_ds003645(tmpdir)