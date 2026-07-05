"""
Unit tests for src/utils.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from utils import (
    calculate_checksum,
    generate_checksums_for_directory,
    setup_logging,
    watchdog,
    TimeoutError,
    ensure_path_exists,
    get_file_size_mb
)


class TestChecksum:
    def test_calculate_checksum_sha256(self, tmp_path):
        """Test checksum calculation for a small file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = calculate_checksum(test_file)
        # Expected SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        
        assert checksum == expected

    def test_calculate_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum(Path("/nonexistent/file.txt"))

    def test_generate_checksums_for_directory(self, tmp_path):
        """Test directory checksum generation."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "subdir" / "file2.txt"
        
        file1.write_text("content1")
        file2.parent.mkdir()
        file2.write_text("content2")
        
        output_file = tmp_path / "checksums.json"
        checksums = generate_checksums_for_directory(tmp_path, output_file)
        
        assert "file1.txt" in checksums
        assert "subdir/file2.txt" in checksums
        
        # Verify JSON file was written
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 2

    def test_generate_checksums_with_extension_filter(self, tmp_path):
        """Test directory checksum generation with extension filter."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.csv"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        output_file = tmp_path / "checksums.json"
        checksums = generate_checksums_for_directory(
            tmp_path, 
            output_file, 
            extensions=[".csv"]
        )
        
        assert "file1.txt" not in checksums
        assert "file2.csv" in checksums


class TestLogging:
    def test_setup_logging_creates_file(self, tmp_path, monkeypatch):
        """Test that setup_logging creates a log file."""
        # Patch LOG_DIR to use temp directory
        monkeypatch.setattr("utils.LOG_DIR", tmp_path)
        
        logger = setup_logging(name="test_logger", log_file=tmp_path / "test.log")
        
        assert logger.handlers
        log_file = tmp_path / "test.log"
        assert log_file.exists()
        
        # Write a log message
        logger.info("Test message")
        
        # Verify content
        with open(log_file) as f:
            content = f.read()
        assert "Test message" in content


class TestWatchdog:
    def test_watchdog_success(self):
        """Test watchdog with a function that completes in time."""
        def quick_func():
            return "success"
        
        result = watchdog(quick_func, timeout_seconds=5)
        assert result == "success"

    @pytest.mark.skipif(os.name == 'nt', reason="SIGALRM not supported on Windows")
    def test_watchdog_timeout(self):
        """Test watchdog triggers timeout."""
        def slow_func():
            time.sleep(10)
            return "done"
        
        with pytest.raises(TimeoutError):
            watchdog(slow_func, timeout_seconds=1)


class TestHelpers:
    def test_ensure_path_exists(self, tmp_path):
        """Test that ensure_path_exists creates directories."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        result = ensure_path_exists(new_dir)
        
        assert result.exists()
        assert result.is_dir()

    def test_get_file_size_mb(self, tmp_path):
        """Test file size calculation."""
        test_file = tmp_path / "size_test.txt"
        # Create a file of known size (1 KB)
        test_file.write_bytes(b"x" * 1024)
        
        size = get_file_size_mb(test_file)
        assert size == 1.0