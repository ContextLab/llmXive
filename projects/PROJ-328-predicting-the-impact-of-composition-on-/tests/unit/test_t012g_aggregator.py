"""
Unit tests for T012g: Write Raw Data to Immutable Store.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.aggregator import calculate_sha256, save_checksums, write_ingestion_status, aggregate_raw_data

class TestAggregator:
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_dir = Path(self.temp_dir.name) / "raw"
        self.raw_dir.mkdir()
        self.checksums_file = Path(self.temp_dir.name) / "checksums.txt"
        self.status_file = self.raw_dir / ".ingestion_status.json"

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_calculate_sha256(self):
        """Test SHA256 calculation."""
        test_file = self.raw_dir / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(test_file)
        expected = hashlib.sha256(test_content).hexdigest()
        
        assert checksum == expected

    def test_save_checksums(self):
        """Test saving checksums to file."""
        checksums = [
            {"filename": "file1.txt", "checksum": "abc123"},
            {"filename": "file2.txt", "checksum": "def456"}
        ]
        save_checksums(checksums, self.checksums_file)
        
        assert self.checksums_file.exists()
        content = self.checksums_file.read_text()
        assert "abc123  file1.txt" in content
        assert "def456  file2.txt" in content

    def test_write_ingestion_status(self):
        """Test writing ingestion status."""
        status = {
            "partial_success": True,
            "successful_files": ["file1.txt"],
            "failed_files": []
        }
        write_ingestion_status(status, self.status_file)
        
        assert self.status_file.exists()
        with open(self.status_file) as f:
            loaded_status = json.load(f)
        assert loaded_status["partial_success"] is True
        assert "file1.txt" in loaded_status["successful_files"]

    def test_aggregate_raw_data_all_success(self):
        """Test aggregation when all files exist."""
        # Create dummy files
        api_file = self.raw_dir / "api_fetched.json"
        api_file.write_text('{"data": "test"}')
        
        lit_file = self.raw_dir / "literature_scraped.csv"
        lit_file.write_text("col1,col2\n1,2")
        
        filtered_file = self.raw_dir / "filtered_raw.csv"
        filtered_file.write_text("col1,col2\n3,4")
        
        status = aggregate_raw_data(
            api_fetched_path=api_file,
            literature_scraped_path=lit_file,
            filtered_raw_path=filtered_file,
            checksums_file=self.checksums_file,
            status_file=self.status_file
        )
        
        assert status["partial_success"] is False
        assert len(status["successful_files"]) == 3
        assert len(status["failed_files"]) == 0
        assert self.checksums_file.exists()
        assert self.status_file.exists()

    def test_aggregate_raw_data_partial_failure(self):
        """Test aggregation when some files are missing."""
        # Create only one file
        api_file = self.raw_dir / "api_fetched.json"
        api_file.write_text('{"data": "test"}')
        
        lit_file = self.raw_dir / "literature_scraped.csv"
        # Do not create filtered_file
        
        status = aggregate_raw_data(
            api_fetched_path=api_file,
            literature_scraped_path=lit_file,
            filtered_raw_path=self.raw_dir / "filtered_raw.csv", # Path exists but file doesn't
            checksums_file=self.checksums_file,
            status_file=self.status_file
        )
        
        assert status["partial_success"] is True
        assert len(status["successful_files"]) == 2
        assert len(status["failed_files"]) == 1
        assert "filtered_raw.csv" in status["failed_files"]

    def test_aggregate_raw_data_no_files(self):
        """Test aggregation when no files exist."""
        status = aggregate_raw_data(
            api_fetched_path=self.raw_dir / "api_fetched.json",
            literature_scraped_path=self.raw_dir / "literature_scraped.csv",
            filtered_raw_path=self.raw_dir / "filtered_raw.csv",
            checksums_file=self.checksums_file,
            status_file=self.status_file
        )
        
        assert status["partial_success"] is False # No files to fail, but also none succeeded
        assert len(status["successful_files"]) == 0
        assert len(status["failed_files"]) == 0
        assert not self.checksums_file.exists()
        assert self.status_file.exists()