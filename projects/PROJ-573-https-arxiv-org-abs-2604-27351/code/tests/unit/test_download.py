"""
Unit tests for dataset download functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.download import (
    compute_dataset_checksum,
    verify_dataset_integrity,
    download_dataset
)


class TestDatasetChecksum:
    """Tests for checksum computation functions."""

    def test_compute_file_sha256_exists(self):
        """Test checksum computation on an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = compute_dataset_checksum(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_path)

    def test_compute_checksum_deterministic(self):
        """Test that checksum is deterministic for same content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum1 = compute_dataset_checksum(temp_path)
            checksum2 = compute_dataset_checksum(temp_path)
            assert checksum1 == checksum2
        finally:
            os.unlink(temp_path)

    def test_compute_checksum_different_content(self):
        """Test that different content produces different checksums."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
            f1.write("content one")
            path1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            f2.write("content two")
            path2 = f2.name

        try:
            checksum1 = compute_dataset_checksum(path1)
            checksum2 = compute_dataset_checksum(path2)
            assert checksum1 != checksum2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_compute_checksum_nonexistent_file(self):
        """Test checksum computation on non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            compute_dataset_checksum("/nonexistent/path/file.txt")


class TestVerifyDatasetIntegrity:
    """Tests for dataset integrity verification."""

    def test_verify_existing_file(self):
        """Test integrity verification on existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = verify_dataset_integrity(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_verify_matching_checksum(self):
        """Test integrity verification with matching checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            expected_checksum = compute_dataset_checksum(temp_path)
            result = verify_dataset_integrity(temp_path, expected_checksum)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_verify_mismatched_checksum(self):
        """Test integrity verification with mismatched checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = verify_dataset_integrity(temp_path, "wrong_checksum")
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_verify_nonexistent_file(self):
        """Test integrity verification on non-existent file."""
        result = verify_dataset_integrity("/nonexistent/path/file.txt")
        assert result is False


class TestDownloadDataset:
    """Tests for dataset download functionality."""

    @patch('src.data.download.Path')
    @patch('src.data.download.load_dataset')
    def test_download_huggingface_dataset(self, mock_load_dataset, mock_path):
        """Test downloading a HuggingFace dataset."""
        # Setup mocks
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = MagicMock()
        mock_dataset.to_pandas().to_csv = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        mock_path_instance = MagicMock()
        mock_path_instance.mkdir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=MagicMock(__str__=lambda self: "/fake/path.csv"))
        mock_path.return_value = mock_path_instance

        # Execute
        with patch('src.data.download.os.path.exists', return_value=True):
            with patch('src.data.download.compute_dataset_checksum', return_value="abc123"):
                path, checksum = download_dataset("test/dataset", max_retries=1, timeout=10)

        # Verify
        assert path is not None
        assert checksum == "abc123"
        mock_load_dataset.assert_called_once()

    @patch('src.data.download.Path')
    @patch('src.data.download.urllib.request')
    def test_download_url(self, mock_urllib, mock_path):
        """Test downloading from a direct URL."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_instance.mkdir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=MagicMock(__str__=lambda self: "/fake/dataset.zip"))
        mock_path.return_value = mock_path_instance

        mock_urllib.urlretrieve = MagicMock()

        # Execute
        with patch('src.data.download.os.path.exists', return_value=True):
            with patch('src.data.download.compute_dataset_checksum', return_value="def456"):
                path, checksum = download_dataset("https://example.com/dataset.zip", max_retries=1, timeout=10)

        # Verify
        assert path is not None
        assert checksum == "def456"
        mock_urllib.urlretrieve.assert_called_once()

    @patch('src.data.download.time.sleep')
    def test_download_retry_on_failure(self, mock_sleep):
        """Test that download retries on failure."""
        with patch('src.data.download.Path') as mock_path:
            with patch('src.data.download.os.path.exists', return_value=False):
                with pytest.raises(RuntimeError) as exc_info:
                    download_dataset("https://example.com/fail", max_retries=2, timeout=1)

                assert "failed after 2 attempts" in str(exc_info.value).lower()

    def test_download_timeout(self):
        """Test that download raises TimeoutError on timeout."""
        with patch('src.data.download.Path') as mock_path:
            with patch('src.data.download.threading.Thread') as mock_thread:
                mock_instance = MagicMock()
                mock_instance.is_alive.return_value = True
                mock_thread.return_value = mock_instance

                with pytest.raises(TimeoutError):
                    download_dataset("https://example.com/slow", max_retries=1, timeout=1)
