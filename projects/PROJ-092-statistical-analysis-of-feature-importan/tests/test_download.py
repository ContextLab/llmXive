"""
Unit tests for the data download and verification module.

Tests verify that the download script handles edge cases and
correctly validates the dataset structure.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.download import calculate_file_hash, verify_dataset

class TestDownloadUtils:
    """Tests for utility functions in download.py"""
    
    def test_calculate_file_hash(self, tmp_path):
        """Test MD5 hash calculation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        file_hash = calculate_file_hash(test_file)
        
        # Known MD5 for "Hello, World!"
        expected_hash = "65a8e27d8879283831b664bd8b7f0ad4"
        assert file_hash == expected_hash
        
    def test_calculate_file_hash_empty(self, tmp_path):
        """Test MD5 hash calculation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        file_hash = calculate_file_hash(test_file)
        
        # Known MD5 for empty string
        expected_hash = "d41d8cd98f00b204e9800998ecf8427e"
        assert file_hash == expected_hash

class TestVerifyDataset:
    """Tests for dataset verification logic."""
    
    def test_verify_nonexistent_file(self, tmp_path):
        """Test verification of a file that doesn't exist."""
        nonexistent = tmp_path / "does_not_exist.csv"
        results = verify_dataset(nonexistent)
        
        assert results["exists"] is False
        assert results["is_valid_csv"] is False
        assert results["row_count"] == 0
        
    def test_verify_empty_file(self, tmp_path):
        """Test verification of an empty CSV file."""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        
        results = verify_dataset(empty_file)
        
        assert results["exists"] is True
        assert results["is_valid_csv"] is False
        assert results["row_count"] == 0
        
    def test_verify_header_only(self, tmp_path):
        """Test verification of a CSV with only a header."""
        header_only = tmp_path / "header_only.csv"
        header_only.write_text("col1;col2;col3\n")
        
        results = verify_dataset(header_only)
        
        assert results["exists"] is True
        assert results["is_valid_csv"] is False
        assert results["column_count"] == 3
        assert results["row_count"] == 0
        
    def test_verify_valid_csv(self, tmp_path):
        """Test verification of a valid CSV file."""
        valid_csv = tmp_path / "valid.csv"
        content = """col1;col2;col3
        1;2;3
        4;5;6
        7;8;9
        """
        valid_csv.write_text(content)
        
        results = verify_dataset(valid_csv)
        
        assert results["exists"] is True
        assert results["is_valid_csv"] is True
        assert results["column_count"] == 3
        assert results["row_count"] == 3
        assert results["size_mb"] > 0
        assert results["hash"] is not None

class TestIntegration:
    """Integration tests that verify the module works as expected."""
    
    def test_module_imports(self):
        """Ensure the download module can be imported without errors."""
        # If we got here, the import succeeded
        assert True
        
    def test_file_hash_consistency(self, tmp_path):
        """Ensure the same file produces the same hash."""
        test_file = tmp_path / "consistent.txt"
        test_file.write_bytes(b"test data")
        
        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex string length
