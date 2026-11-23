"""
tests/unit/test_ingestion_checksum.py
Unit tests for T016: Checksum generation and storage logic.
"""

import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the function to test
from code.data.ingestion import generate_checksum, calculate_file_hash

class TestChecksumGeneration:
    """Tests for checksum generation functionality."""

    def test_generate_checksum_creates_file(self, tmp_path):
        """Test that generate_checksum creates a valid JSON file."""
        # Create a temporary CSV file
        test_data = "col1,col2\n1,2\n3,4"
        test_file = tmp_path / "test_data.csv"
        test_file.write_text(test_data)

        output_file = tmp_path / "checksum.json"

        # Run the function
        result = generate_checksum(test_file, output_path=output_file)

        # Verify file exists
        assert output_file.exists()

        # Verify result content
        assert result['path'] == str(test_file.absolute())
        assert 'hash' in result
        assert len(result['hash']) == 64 # SHA-256 hex length
        assert result['size_bytes'] == len(test_data.encode('utf-8'))
        assert 'timestamp' in result

        # Verify JSON content matches result
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['hash'] == result['hash']
        assert saved_data['size_bytes'] == result['size_bytes']

    def test_calculate_file_hash_consistency(self, tmp_path):
        """Test that calculate_file_hash returns consistent results."""
        test_file = tmp_path / "consistent.csv"
        test_file.write_text("data")

        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_calculate_file_hash_file_not_found(self):
        """Test that calculate_file_hash raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            calculate_file_hash("non_existent_file.csv")

    def test_generate_checksum_no_output_path(self, tmp_path):
        """Test that generate_checksum works without saving to disk."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("test")

        result = generate_checksum(test_file) # No output_path

        assert 'hash' in result
        # No file should be created since output_path was None
        # (We can't easily check non-creation in tmp_path without more setup, 
        # but the function returns the dict as expected)

    def test_checksum_matches_content_change(self, tmp_path):
        """Test that checksum changes when file content changes."""
        test_file = tmp_path / "dynamic.csv"
        test_file.write_text("original")
        hash1 = calculate_file_hash(test_file)

        test_file.write_text("modified")
        hash2 = calculate_file_hash(test_file)

        assert hash1 != hash2

if __name__ == '__main__':
    pytest.main([__file__, "-v"])