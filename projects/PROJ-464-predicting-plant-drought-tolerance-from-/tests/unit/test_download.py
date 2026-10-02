import os
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the functions we want to test
# Note: We assume these are in code/download_images.py
# Adjust import path if necessary based on project structure
import sys
sys.path.insert(0, 'code')

from download_images import (
    compute_sha256,
    load_existing_checksums,
    save_checksums,
    verify_checksums,
    get_hf_files_list
)


class TestChecksumFunctions:
    
    def test_compute_sha256(self, tmp_path):
        """Test that SHA256 is computed correctly."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums."""
        checksums = {"file1.jpg": "abc123", "file2.jpg": "def456"}
        checksum_file = tmp_path / "checksums.json"
        
        # Patch the global CHECKSUM_FILE constant or pass path
        # Since the functions use global constants, we need to be careful
        # For this test, we'll test the logic directly
        
        with patch('download_images.CHECKSUM_FILE', checksum_file):
            save_checksums(checksums)
            loaded = load_existing_checksums()
            assert loaded == checksums
    
    def test_verify_checksums_pass(self, tmp_path):
        """Test successful checksum verification."""
        # Create test files
        file1 = tmp_path / "file1.jpg"
        file1.write_bytes(b"data1")
        file2 = tmp_path / "file2.jpg"
        file2.write_bytes(b"data2")
        
        # Create checksums
        checksums = {
            "file1.jpg": compute_sha256(file1),
            "file2.jpg": compute_sha256(file2)
        }
        
        # Verify
        result = verify_checksums([file1, file2], checksums)
        assert result is True
    
    def test_verify_checksums_fail(self, tmp_path):
        """Test checksum verification failure."""
        # Create test files
        file1 = tmp_path / "file1.jpg"
        file1.write_bytes(b"data1")
        
        # Create wrong checksum
        wrong_checksums = {
            "file1.jpg": "wrong_hash_value"
        }
        
        # Verify should raise RuntimeError
        with pytest.raises(RuntimeError, match="Data integrity check failed for NPPN images."):
            verify_checksums([file1], wrong_checksums)
    
    def test_verify_checksums_generates_manifest(self, tmp_path):
        """Test that verify_checksums generates a manifest if none exists."""
        file1 = tmp_path / "file1.jpg"
        file1.write_bytes(b"data1")
        
        # No existing checksums
        with patch('download_images.CHECKSUM_FILE', tmp_path / "new_checksums.json"):
            result = verify_checksums([file1], {})
            assert result is True
            
            # Check that file was created
            assert (tmp_path / "new_checksums.json").exists()


class TestHFIntegration:
    
    @patch('download_images.HfApi')
    def test_get_hf_files_list_success(self, MockHfApi):
        """Test successful file listing from HF."""
        mock_instance = MagicMock()
        MockHfApi.return_value = mock_instance
        mock_instance.list_repo_files.return_value = [
            "root1.jpg", "root2.png", "readme.md"
        ]
        
        files = get_hf_files_list()
        
        assert len(files) == 2
        assert "root1.jpg" in files
        assert "root2.png" in files
    
    @patch('download_images.HfApi')
    def test_get_hf_files_list_failure(self, MockHfApi):
        """Test failure to access HF repository."""
        from huggingface_hub.utils import RepositoryNotFoundError
        mock_instance = MagicMock()
        MockHfApi.return_value = mock_instance
        mock_instance.list_repo_files.side_effect = RepositoryNotFoundError("Not found")
        
        with pytest.raises(RuntimeError, match="No real NPPN root images found. Pipeline cannot proceed."):
            get_hf_files_list()
    
    @patch('download_images.HfApi')
    def test_get_hf_files_list_no_images(self, MockHfApi):
        """Test repository with no image files."""
        mock_instance = MagicMock()
        MockHfApi.return_value = mock_instance
        mock_instance.list_repo_files.return_value = ["readme.md", "data.txt"]
        
        files = get_hf_files_list()
        assert len(files) == 0