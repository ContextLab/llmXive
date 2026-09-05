"""
Unit tests for the LiteratureAggregator checksum functionality.

These tests verify that:
1. Raw data files are created correctly
2. SHA256 checksums are calculated correctly
3. Checksums are appended to the checksums file
"""

import os
import sys
import json
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingestion.aggregator import LiteratureAggregator
from utils.error_handlers import IngestionError, ConfigurationError


class TestLiteratureAggregatorChecksums:
    """Test cases for LiteratureAggregator checksum functionality."""
    
    @pytest.fixture
    def temp_raw_dir(self, tmp_path):
        """Create a temporary raw directory for testing."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        return raw_dir
    
    @pytest.fixture
    def aggregator(self, temp_raw_dir):
        """Create an aggregator instance with a temporary raw directory."""
        with patch('ingestion.aggregator.get_data_raw_dir', return_value=temp_raw_dir):
            with patch('ingestion.aggregator.get_config', return_value={}):
                aggregator = LiteratureAggregator()
                # Override checksums file path
                aggregator.checksums_file = temp_raw_dir.parent / "checksums.txt"
                return aggregator
    
    def test_calculate_sha256(self, aggregator, temp_raw_dir):
        """Test SHA256 checksum calculation."""
        # Create a test file
        test_file = temp_raw_dir / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        # Calculate checksum
        checksum = aggregator._calculate_sha256(test_file)
        
        # Verify checksum
        expected = hashlib.sha256(test_content.encode()).hexdigest()
        assert checksum == expected
    
    def test_append_checksum(self, aggregator, temp_raw_dir):
        """Test checksum appending to checksums file."""
        # Create a test file
        test_file = temp_raw_dir / "test.txt"
        test_file.write_text("Test content")
        
        # Calculate and append checksum
        checksum = aggregator._calculate_sha256(test_file)
        aggregator._append_checksum(test_file, checksum)
        
        # Verify checksums file
        assert aggregator.checksums_file.exists()
        content = aggregator.checksums_file.read_text()
        
        assert test_file.name in content
        assert checksum in content
    
    def test_save_raw_data_json(self, aggregator, temp_raw_dir):
        """Test saving raw data as JSON."""
        test_data = [
            {"id": 1, "name": "Test1"},
            {"id": 2, "name": "Test2"}
        ]
        
        # Save data
        file_path = aggregator._save_raw_data(test_data, "test.json", "json")
        
        # Verify file exists
        assert file_path.exists()
        assert file_path.name == "test.json"
        
        # Verify content
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
        
        # Verify checksum was appended
        assert aggregator.checksums_file.exists()
        content = aggregator.checksums_file.read_text()
        assert "test.json" in content
    
    def test_save_raw_data_csv(self, aggregator, temp_raw_dir):
        """Test saving raw data as CSV."""
        test_data = [
            {"col1": "a", "col2": 1},
            {"col1": "b", "col2": 2}
        ]
        
        # Save data
        file_path = aggregator._save_raw_data(test_data, "test.csv", "csv")
        
        # Verify file exists
        assert file_path.exists()
        assert file_path.name == "test.csv"
        
        # Verify checksum was appended
        assert aggregator.checksums_file.exists()
        content = aggregator.checksums_file.read_text()
        assert "test.csv" in content
    
    def test_save_raw_data_invalid_type(self, aggregator, temp_raw_dir):
        """Test that invalid source type raises error."""
        test_data = [{"id": 1}]
        
        with pytest.raises(IngestionError, match="Unsupported source type"):
            aggregator._save_raw_data(test_data, "test.xyz", "xyz")
    
    def test_multiple_checksums_appended(self, aggregator, temp_raw_dir):
        """Test that multiple checksums are appended correctly."""
        # Save first file
        data1 = [{"id": 1}]
        path1 = aggregator._save_raw_data(data1, "file1.json", "json")
        
        # Save second file
        data2 = [{"id": 2}]
        path2 = aggregator._save_raw_data(data2, "file2.json", "json")
        
        # Verify both checksums are in the file
        content = aggregator.checksums_file.read_text()
        lines = content.strip().split('\n')
        
        assert len(lines) >= 2
        assert "file1.json" in content
        assert "file2.json" in content
    
    def test_checksums_file_created_if_not_exists(self, temp_raw_dir):
        """Test that checksums file is created if it doesn't exist."""
        checksums_file = temp_raw_dir.parent / "checksums.txt"
        
        # Ensure file doesn't exist
        if checksums_file.exists():
            checksums_file.unlink()
        
        # Create aggregator (should create checksums file)
        with patch('ingestion.aggregator.get_data_raw_dir', return_value=temp_raw_dir):
            with patch('ingestion.aggregator.get_config', return_value={}):
                aggregator = LiteratureAggregator()
                aggregator.checksums_file = checksums_file
        
        # Verify file was created
        assert checksums_file.exists()