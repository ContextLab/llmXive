"""
Unit tests for code/data/download.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# We need to mock the datasets library to avoid actual network calls in unit tests
# and to simulate the specific error conditions (e.g., subset not found).
from unittest.mock import patch, MagicMock, mock_open
import hashlib

# Import the module under test
# Note: We need to adjust the path if running from the project root
import sys
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.data import download


class TestDownloadChecksum:
    """Tests for the checksum computation logic."""

    def test_compute_file_checksum(self, tmp_path):
        """Test that compute_file_checksum correctly hashes a file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Compute expected hash manually
        expected_hash = hashlib.sha256(content).hexdigest()

        # Call the function
        result = download.compute_file_checksum(test_file)

        assert result == expected_hash

    def test_compute_file_checksum_large(self, tmp_path):
        """Test checksum with a larger file to ensure chunking works."""
        test_file = tmp_path / "large.bin"
        content = b"x" * (1024 * 1024)  # 1MB
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        result = download.compute_file_checksum(test_file)

        assert result == expected_hash


class TestDownloadDataset:
    """Tests for the download_dataset logic."""

    def test_download_success(self, tmp_path, monkeypatch):
        """Test successful download and parquet saving."""
        # Setup paths
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True)
        
        output_file = raw_dir / "omnidoc_tokenbench.parquet"
        checksum_file = results_dir / "checksum.json"

        # Mock the dataset object
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=100)
        mock_ds.features = {"image": "Image", "text": "Text"}
        mock_ds.to_parquet = MagicMock()

        # Patch the load_dataset function
        with patch.object(download, 'load_dataset', return_value=mock_ds):
            # We need to patch the OUTPUT_DIR and CHECKSUM_OUTPUT temporarily
            # Since they are module-level constants, we patch the module attributes
            original_output_dir = download.OUTPUT_DIR
            original_checksum_output = download.CHECKSUM_OUTPUT
            
            # Create a mock Path that writes to tmp_path
            # We can't easily mock the Path class globally, so we patch the specific calls
            # Actually, it's easier to just patch the functions that write files
            with patch.object(download.OUTPUT_DIR, 'mkdir'), \
                 patch.object(download.CHECKSUM_OUTPUT.parent, 'mkdir'), \
                 patch('builtins.open', mock_open()) as mock_file, \
                 patch.object(download, 'compute_file_checksum', return_value="abc123"):
                 
                 # Temporarily change module constants to point to tmp_path
                 download.OUTPUT_DIR = raw_dir
                 download.CHECKSUM_OUTPUT = checksum_file
                 
                 try:
                     download.download_dataset()
                     
                     # Verify to_parquet was called
                     mock_ds.to_parquet.assert_called_once()
                     # Verify checksum file was written
                     assert mock_file.called
                 finally:
                     # Restore
                     download.OUTPUT_DIR = original_output_dir
                     download.CHECKSUM_OUTPUT = original_checksum_output

    def test_download_subset_not_found(self, tmp_path, monkeypatch):
        """Test that a specific error is raised when subset is not found."""
        # Patch load_dataset to raise FileNotFoundError
        with patch.object(download, 'load_dataset', side_effect=FileNotFoundError("Config 'omnidoc-tokenbench' not found")):
            # We expect the function to raise FileNotFoundError
            with pytest.raises(FileNotFoundError, match="subset.*not found"):
                download.download_dataset()

    def test_download_runtime_error(self, tmp_path):
        """Test that a RuntimeError is raised for other download failures."""
        with patch.object(download, 'load_dataset', side_effect=Exception("Network error")):
            with pytest.raises(RuntimeError, match="Failed to download dataset"):
                download.download_dataset()

    def test_main_success(self, tmp_path, monkeypatch):
        """Test the main entry point on success."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=10)
        mock_ds.features = {}
        mock_ds.to_parquet = MagicMock()
        
        with patch.object(download, 'load_dataset', return_value=mock_ds), \
             patch.object(download, 'OUTPUT_DIR', tmp_path), \
             patch.object(download, 'CHECKSUM_OUTPUT', tmp_path / "checksum.json"), \
             patch.object(Path, 'mkdir'), \
             patch('builtins.open', mock_open()), \
             patch.object(download, 'compute_file_checksum', return_value="hash"):
            
                result = download.main()
                assert result == 0

    def test_main_failure(self, tmp_path):
        """Test the main entry point on failure."""
        with patch.object(download, 'load_dataset', side_effect=FileNotFoundError("Not found")):
            result = download.main()
            assert result == 1
