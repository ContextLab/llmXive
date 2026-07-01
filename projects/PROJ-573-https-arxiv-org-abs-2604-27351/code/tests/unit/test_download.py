"""
Unit tests for dataset download functionality.
"""
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
    _download_huggingface_dataset
)

class TestDatasetChecksum:
    def test_compute_checksum(self, tmp_path):
        """Test checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_dataset_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

    def test_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        checksum1 = compute_dataset_checksum(test_file)
        checksum2 = compute_dataset_checksum(test_file)
        
        assert checksum1 == checksum2

    def test_checksum_different_content(self, tmp_path):
        """Test that checksum differs for different content."""
        test_file1 = tmp_path / "test1.txt"
        test_file2 = tmp_path / "test2.txt"
        
        test_file1.write_text("Content 1")
        test_file2.write_text("Content 2")
        
        checksum1 = compute_dataset_checksum(test_file1)
        checksum2 = compute_dataset_checksum(test_file2)
        
        assert checksum1 != checksum2

class TestVerifyDatasetIntegrity:
    def test_verify_existing_file(self, tmp_path):
        """Test verification of existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        assert verify_dataset_integrity(test_file) is True

    def test_verify_missing_file(self, tmp_path):
        """Test verification of missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        
        assert verify_dataset_integrity(missing_file) is False

    def test_verify_checksum_match(self, tmp_path):
        """Test verification with matching checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        checksum = compute_dataset_checksum(test_file)
        
        assert verify_dataset_integrity(test_file, checksum) is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test verification with mismatched checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        wrong_checksum = "a" * 64
        
        assert verify_dataset_integrity(test_file, wrong_checksum) is False

class TestDownloadDataset:
    @patch('src.data.download.requests.get')
    def test_download_url_success(self, mock_get, tmp_path):
        """Test successful URL download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test content"]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Change to temp directory for test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Ensure data dir exists
            data_dir = tmp_path / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            path, checksum = download_dataset(
                "https://example.com/dataset.txt",
                max_retries=1,
                timeout=10
            )
            
            assert path.exists()
            assert len(checksum) == 64
        finally:
            os.chdir(original_cwd)

    @patch('src.data.download.requests.get')
    def test_download_url_failure(self, mock_get, tmp_path):
        """Test download failure after retries."""
        mock_get.side_effect = Exception("Network error")
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            data_dir = tmp_path / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            with pytest.raises(Exception, match="Failed to download"):
                download_dataset(
                    "https://example.com/dataset.txt",
                    max_retries=2,
                    timeout=10
                )
        finally:
            os.chdir(original_cwd)

    @patch('src.data.download.load_dataset')
    def test_download_huggingface_dataset(self, mock_load_dataset, tmp_path):
        """Test HuggingFace dataset download."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.save_to_disk = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            data_dir = tmp_path / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            path, checksum = _download_huggingface_dataset(
                "UCI_HAR",
                data_dir,
                timeout=10
            )
            
            assert path.exists() or path.is_dir()
            assert len(checksum) == 64
        finally:
            os.chdir(original_cwd)

class TestEnsureDataDirs:
    def test_ensure_data_dirs_creates_directories(self, tmp_path):
        """Test that ensure_data_dirs creates required directories."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_data_dirs()
            
            assert (tmp_path / "data").exists()
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
        finally:
            os.chdir(original_cwd)
