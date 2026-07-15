"""
Unit tests for code/loaders.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from code.loaders import (
    ingest_csv,
    _compute_file_hash,
    _save_checksum,
    _verify_checksum
)


class TestIngestCSV:
    """Tests for the ingest_csv function."""

    def test_ingest_valid_csv(self, tmp_path):
        """Test ingesting a valid CSV file."""
        # Create a temporary CSV file
        csv_content = """col1,col2,col3
        1,2.5,hello
        2,3.5,world
        3,4.5,test"""
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        # Ingest the file
        df = ingest_csv(csv_file)
        
        # Verify results
        assert len(df) == 3
        assert len(df.columns) == 3
        assert list(df.columns) == ["col1", "col2", "col3"]
        assert df["col1"].iloc[0] == 1
        assert df["col2"].iloc[0] == 2.5
        assert df["col3"].iloc[0] == "hello"

    def test_ingest_empty_file(self, tmp_path):
        """Test that ingesting an empty file raises ValueError."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        with pytest.raises(ValueError, match="File is empty"):
            ingest_csv(csv_file)

    def test_ingest_nonexistent_file(self, tmp_path):
        """Test that ingesting a non-existent file raises FileNotFoundError."""
        csv_file = tmp_path / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError):
            ingest_csv(csv_file)

    def test_ingest_with_na_values(self, tmp_path):
        """Test handling of NA values."""
        csv_content = """col1,col2
        1,2
        2,NA
        3,"""
        
        csv_file = tmp_path / "na_test.csv"
        csv_file.write_text(csv_content)
        
        df = ingest_csv(csv_file, na_values=["NA", ""])
        
        assert len(df) == 3
        assert pd.isna(df["col2"].iloc[1])
        assert pd.isna(df["col2"].iloc[2])


class TestChecksumFunctions:
    """Tests for checksum utilities."""

    def test_compute_file_hash(self, tmp_path):
        """Test file hash computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hash1 = _compute_file_hash(test_file)
        hash2 = _compute_file_hash(test_file)
        
        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_save_and_verify_checksum(self, tmp_path):
        """Test saving and verifying checksums."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum_file = tmp_path / "checksums.json"
        dataset_id = "test_dataset"
        
        # Save checksum
        checksum = _compute_file_hash(test_file)
        _save_checksum(dataset_id, checksum, checksum_file)
        
        # Verify checksum
        assert _verify_checksum(test_file, dataset_id, checksum_file) is True
        
        # Modify file and verify failure
        test_file.write_text("modified content")
        assert _verify_checksum(test_file, dataset_id, checksum_file) is False

    def test_verify_nonexistent_checksum_file(self, tmp_path):
        """Test verification when checksum file doesn't exist."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum_file = tmp_path / "nonexistent.json"
        
        # Should return True (no checksum to verify against)
        assert _verify_checksum(test_file, "test_id", checksum_file) is True

    def test_verify_corrupt_checksum_file(self, tmp_path):
        """Test verification with corrupt checksum file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum_file = tmp_path / "checksums.json"
        checksum_file.write_text("not valid json")
        
        # Should return True (skip verification on corrupt file)
        assert _verify_checksum(test_file, "test_id", checksum_file) is True


class TestLoadersIntegration:
    """Integration tests for loader functions."""

    def test_attributes_preserved(self, tmp_path):
        """Test that DataFrame attributes are preserved."""
        csv_content = """col1,col2
        1,2
        3,4"""
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        df = ingest_csv(csv_file)
        
        assert 'original_columns' in df.attrs
        assert df.attrs['original_columns'] == ["col1", "col2"]

    def test_large_file_handling(self, tmp_path):
        """Test handling of larger files."""
        # Generate a larger CSV
        n_rows = 1000
        csv_content = "col1,col2,col3\n"
        for i in range(n_rows):
            csv_content += f"{i},{i*2},{i*3}\n"
        
        csv_file = tmp_path / "large.csv"
        csv_file.write_text(csv_content)
        
        df = ingest_csv(csv_file)
        
        assert len(df) == n_rows
        assert len(df.columns) == 3
