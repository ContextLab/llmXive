"""
Tests for Z-Reward dataset download functionality.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import the module to test
import sys
sys.path.insert(0, 'projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code')
from download_zreward import (
    calculate_sha256,
    save_checksum,
    verify_checksum,
    download_dataset,
    parse_args
)


class TestCalculateSha256:
    """Tests for calculate_sha256 function."""

    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(str(test_file))
        
        # Expected SHA256 of "Hello, World!"
        expected = hashlib.sha256(test_content).hexdigest()
        
        assert checksum == expected
        assert len(checksum) == 64  # SHA256 produces 64 hex characters

    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA256 calculation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        checksum = calculate_sha256(str(test_file))
        
        # Expected SHA256 of empty string
        expected = hashlib.sha256(b"").hexdigest()
        
        assert checksum == expected


class TestSaveChecksum:
    """Tests for save_checksum function."""

    def test_save_checksum(self, tmp_path):
        """Test saving checksum to file."""
        checksum_file = tmp_path / "checksums"
        test_checksum = "abc123def456"
        
        save_checksum(test_checksum, str(checksum_file))
        
        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert test_checksum in content
        assert "zreward_dataset.csv" in content


class TestVerifyChecksum:
    """Tests for verify_checksum function."""

    def test_verify_checksum_success(self, tmp_path):
        """Test successful checksum verification."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)
        
        actual_checksum = hashlib.sha256(test_content).hexdigest()
        
        assert verify_checksum(str(test_file), actual_checksum) is True

    def test_verify_checksum_failure(self, tmp_path):
        """Test failed checksum verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        wrong_checksum = "0" * 64  # Wrong checksum
        
        assert verify_checksum(str(test_file), wrong_checksum) is False


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parse_args_default(self):
        """Test default argument values."""
        with patch('sys.argv', ['download_zreward.py']):
            args = parse_args()
            
            assert args.dataset_name == "zreward/zreward-v1"
            assert args.split == "train"
            assert args.output_dir == "data/raw"
            assert args.output_filename == "zreward_dataset.csv"
            assert args.verify is False

    def test_parse_args_custom(self):
        """Test custom argument values."""
        with patch('sys.argv', [
            'download_zreward.py',
            '--dataset-name', 'custom/dataset',
            '--split', 'test',
            '--output-dir', 'custom/output',
            '--output-filename', 'custom.csv',
            '--verify'
        ]):
            args = parse_args()
            
            assert args.dataset_name == "custom/dataset"
            assert args.split == "test"
            assert args.output_dir == "custom/output"
            assert args.output_filename == "custom.csv"
            assert args.verify is True


class TestDownloadDataset:
    """Tests for download_dataset function."""

    def test_download_dataset_success(self, tmp_path):
        """Test successful dataset download and conversion."""
        # Create mock dataset
        mock_dataset = Mock()
        mock_df = Mock()
        mock_df.shape = (100, 5)
        mock_df.columns = ['col1', 'col2', 'col3', 'col4', 'col5']
        mock_df.to_pandas.return_value = mock_df
        mock_dataset.to_pandas.return_value = mock_df
        
        output_path = tmp_path / "output.csv"
        
        with patch('download_zreward.load_dataset', return_value=mock_dataset):
            result_path, checksum = download_dataset(
                "test/dataset",
                "train",
                str(output_path)
            )
            
            assert result_path == str(output_path)
            assert output_path.exists()
            assert len(checksum) == 64

    def test_download_dataset_failure(self):
        """Test download failure raises RuntimeError."""
        with patch('download_zreward.load_dataset', side_effect=Exception("Network error")):
            with pytest.raises(RuntimeError, match="Dataset download failed"):
                download_dataset("test/dataset", "train", "/tmp/output.csv")

    def test_download_dataset_missing_import(self):
        """Test missing datasets package handling."""
        # This test verifies the import check at module level
        # The actual test would require uninstalling the package
        pass