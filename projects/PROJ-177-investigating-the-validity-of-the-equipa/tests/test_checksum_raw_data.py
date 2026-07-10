"""
Tests for code/checksum_raw_data.py
"""
import hashlib
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from checksum_raw_data import calculate_sha256, get_raw_data_files, generate_checksums, write_checksum_log


class TestCalculateSha256:
    """Tests for the SHA-256 calculation function."""
    
    def test_known_string_hash(self, tmp_path):
        """Test hash calculation with a known string."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_empty_file_hash(self, tmp_path):
        """Test hash calculation with an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_large_file_hash(self, tmp_path):
        """Test hash calculation with a larger file to ensure chunking works."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file with known content
        content = b"X" * (1024 * 1024)
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash


class TestGetRawDataFiles:
    """Tests for file discovery."""
    
    def test_no_files(self, tmp_path):
        """Test when directory is empty."""
        # Create a temporary raw data directory
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Temporarily override the global constant
        import checksum_raw_data
        original_dir = checksum_raw_data.RAW_DATA_DIR
        checksum_raw_data.RAW_DATA_DIR = raw_dir
        
        try:
            files = get_raw_data_files()
            assert files == []
        finally:
            checksum_raw_data.RAW_DATA_DIR = original_dir
    
    def test_single_file(self, tmp_path):
        """Test discovery of a single file."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        test_file = raw_dir / "test.csv"
        test_file.write_text("data")
        
        import checksum_raw_data
        original_dir = checksum_raw_data.RAW_DATA_DIR
        checksum_raw_data.RAW_DATA_DIR = raw_dir
        
        try:
            files = get_raw_data_files()
            assert len(files) == 1
            assert files[0].name == "test.csv"
        finally:
            checksum_raw_data.RAW_DATA_DIR = original_dir
    
    def test_subdirectory_files(self, tmp_path):
        """Test discovery of files in subdirectories."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        subdir = raw_dir / "subdir"
        subdir.mkdir()
        
        file1 = raw_dir / "file1.csv"
        file2 = subdir / "file2.csv"
        file1.write_text("data1")
        file2.write_text("data2")
        
        import checksum_raw_data
        original_dir = checksum_raw_data.RAW_DATA_DIR
        checksum_raw_data.RAW_DATA_DIR = raw_dir
        
        try:
            files = get_raw_data_files()
            assert len(files) == 2
            # Files should be sorted
            assert "file1.csv" in str(files[0])
            assert "file2.csv" in str(files[1])
        finally:
            checksum_raw_data.RAW_DATA_DIR = original_dir
    
    def test_skips_hidden_files(self, tmp_path):
        """Test that hidden files are skipped."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        visible_file = raw_dir / "visible.csv"
        hidden_file = raw_dir / ".hidden.csv"
        visible_file.write_text("data")
        hidden_file.write_text("hidden")
        
        import checksum_raw_data
        original_dir = checksum_raw_data.RAW_DATA_DIR
        checksum_raw_data.RAW_DATA_DIR = raw_dir
        
        try:
            files = get_raw_data_files()
            assert len(files) == 1
            assert files[0].name == "visible.csv"
        finally:
            checksum_raw_data.RAW_DATA_DIR = original_dir


class TestGenerateChecksums:
    """Tests for checksum generation."""
    
    def test_generates_correct_checksums(self, tmp_path):
        """Test that checksums are generated correctly."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        test_file = raw_dir / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)
        
        import checksum_raw_data
        original_dir = checksum_raw_data.RAW_DATA_DIR
        checksum_raw_data.RAW_DATA_DIR = raw_dir
        checksum_raw_data.CHECKSUM_LOG_FILE = tmp_path / "test.log"
        
        try:
            checksums = generate_checksums()
            assert len(checksums) == 1
            
            expected_hash = hashlib.sha256(content).hexdigest()
            # The key should contain the relative path
            key = list(checksums.keys())[0]
            assert "test.txt" in key
            assert checksums[key] == expected_hash
        finally:
            checksum_raw_data.RAW_DATA_DIR = original_dir
            checksum_raw_data.CHECKSUM_LOG_FILE = Path("data/raw_checksums.log")


class TestWriteChecksumLog:
    """Tests for log file writing."""
    
    def test_writes_log_file(self, tmp_path):
        """Test that log file is written correctly."""
        test_file = tmp_path / "test.log"
        checksums = {
            "data/raw/file1.csv": "abc123",
            "data/raw/file2.csv": "def456"
        }
        
        write_checksum_log(checksums)
        
        # Overwrite to test with custom path
        import checksum_raw_data
        original_log = checksum_raw_data.CHECKSUM_LOG_FILE
        checksum_raw_data.CHECKSUM_LOG_FILE = test_file
        
        try:
            write_checksum_log(checksums)
            assert test_file.exists()
            
            content = test_file.read_text()
            assert "Raw Data Checksum Log" in content
            assert "abc123" in content
            assert "def456" in content
            assert "file1.csv" in content
            assert "file2.csv" in content
        finally:
            checksum_raw_data.CHECKSUM_LOG_FILE = original_log
    
    def test_handles_empty_checksums(self, tmp_path):
        """Test writing log with no files."""
        import checksum_raw_data
        original_log = checksum_raw_data.CHECKSUM_LOG_FILE
        checksum_raw_data.CHECKSUM_LOG_FILE = tmp_path / "empty.log"
        
        try:
            write_checksum_log({})
            content = checksum_raw_data.CHECKSUM_LOG_FILE.read_text()
            assert "No files found" in content
        finally:
            checksum_raw_data.CHECKSUM_LOG_FILE = original_log
