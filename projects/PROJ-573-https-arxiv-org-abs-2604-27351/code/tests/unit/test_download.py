import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.download import (
    ensure_data_dirs,
    compute_dataset_checksum,
    verify_dataset_integrity,
    download_dataset,
    compute_directory_checksum
)
import hashlib

class TestEnsureDataDirs:
    def test_creates_directories(self, tmp_path):
        """Test that ensure_data_dirs creates necessary directories."""
        result = ensure_data_dirs(tmp_path)
        
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()
        assert result == tmp_path

    def test_uses_existing_directories(self, tmp_path):
        """Test that ensure_data_dirs doesn't fail on existing directories."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "processed").mkdir()
        
        result = ensure_data_dirs(tmp_path)
        
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()

class TestDatasetChecksum:
    def test_compute_checksum(self, tmp_path):
        """Test checksum computation for a file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_dataset_checksum(test_file)
        
        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected

    def test_different_content_different_checksum(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_bytes(b"Content 1")
        file2.write_bytes(b"Content 2")
        
        checksum1 = compute_dataset_checksum(file1)
        checksum2 = compute_dataset_checksum(file2)
        
        assert checksum1 != checksum2

class TestVerifyDatasetIntegrity:
    def test_verify_with_matching_checksum(self, tmp_path):
        """Test verification with matching checksum."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)
        
        checksum = compute_dataset_checksum(test_file)
        
        assert verify_dataset_integrity(test_file, checksum) is True

    def test_verify_with_mismatched_checksum(self, tmp_path):
        """Test verification with mismatched checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        assert verify_dataset_integrity(test_file, "wrong_checksum") is False

    def test_verify_missing_file(self, tmp_path):
        """Test verification of non-existent file."""
        non_existent = tmp_path / "nonexistent.txt"
        
        assert verify_dataset_integrity(non_existent) is False

class TestDownloadDataset:
    @patch('src.data.download.load_dataset')
    @patch('src.data.download.compute_directory_checksum')
    def test_download_hf_dataset(self, mock_checksum, mock_load, tmp_path):
        """Test downloading from HuggingFace."""
        mock_dataset = MagicMock()
        mock_dataset.__contains__.return_value = True
        mock_dataset.__getitem__.return_value = MagicMock()
        mock_load.return_value = mock_dataset
        mock_checksum.return_value = "test_checksum"
        
        path, checksum = download_dataset(
            url="test_dataset",
            output_dir=tmp_path,
            max_retries=1
        )
        
        mock_load.assert_called_once_with("test_dataset")
        assert checksum == "test_checksum"
        assert os.path.exists(path)

    @patch('src.data.download.requests.get')
    def test_download_url(self, mock_get, tmp_path):
        """Test downloading from URL."""
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        url = "https://example.com/dataset.zip"
        path, checksum = download_dataset(
            url=url,
            output_dir=tmp_path,
            max_retries=1
        )
        
        mock_get.assert_called_once()
        assert os.path.exists(path)

    def test_download_failure(self, tmp_path):
        """Test that download raises after max retries."""
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Network error")
            
            with pytest.raises(RuntimeError, match="Failed to download"):
                download_dataset(
                    url="test",
                    output_dir=tmp_path,
                    max_retries=2
                )

class TestComputeDirectoryChecksum:
    def test_directory_checksum(self, tmp_path):
        """Test checksum computation for a directory."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_bytes(b"Content 1")
        file2.write_bytes(b"Content 2")
        
        checksum = compute_directory_checksum(tmp_path)
        
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

    def test_empty_directory(self, tmp_path):
        """Test checksum for empty directory."""
        checksum = compute_directory_checksum(tmp_path)
        assert len(checksum) == 64