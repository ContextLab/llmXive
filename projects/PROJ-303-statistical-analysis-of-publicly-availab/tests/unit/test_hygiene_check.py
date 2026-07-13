"""
Unit tests for src/scripts/hygiene_check.py
"""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the functions to test
# We need to import the module directly to access internal helpers
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scripts.hygiene_check import (
    compute_sha256,
    scan_raw_data_directory,
    generate_hygiene_report,
    write_hygiene_report
)


class TestComputeSha256:
    def test_hash_of_known_string(self, tmp_path):
        """Test SHA256 calculation on a known file content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_hash_of_empty_file(self, tmp_path):
        """Test SHA256 calculation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_binary_file(self, tmp_path):
        """Test SHA256 calculation on a binary file."""
        test_file = tmp_path / "binary.bin"
        content = bytes(range(256))
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash


class TestScanRawDataDirectory:
    def test_scan_single_file(self, tmp_path):
        """Test scanning a directory with a single file."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("data")

        files = scan_raw_data_directory(tmp_path)
        assert len(files) == 1
        assert files[0] == test_file

    def test_scan_nested_directories(self, tmp_path):
        """Test scanning a directory with nested subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        file1.write_text("data1")
        file2.write_text("data2")

        files = scan_raw_data_directory(tmp_path)
        assert len(files) == 2
        assert file1 in files
        assert file2 in files

    def test_skip_hidden_files(self, tmp_path):
        """Test that hidden files are skipped."""
        visible_file = tmp_path / "visible.txt"
        hidden_file = tmp_path / ".hidden.txt"
        visible_file.write_text("data")
        hidden_file.write_text("data")

        files = scan_raw_data_directory(tmp_path)
        assert len(files) == 1
        assert visible_file in files
        assert hidden_file not in files

    def test_skip_tmp_files(self, tmp_path):
        """Test that .tmp files are skipped."""
        valid_file = tmp_path / "valid.txt"
        tmp_file = tmp_path / "temp.tmp"
        valid_file.write_text("data")
        tmp_file.write_text("data")

        files = scan_raw_data_directory(tmp_path)
        assert len(files) == 1
        assert valid_file in files
        assert tmp_file not in files

    def test_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        files = scan_raw_data_directory(tmp_path)
        assert len(files) == 0

    def test_non_existent_directory(self, tmp_path):
        """Test scanning a non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            scan_raw_data_directory(tmp_path / "non_existent")


class TestGenerateHygieneReport:
    def test_report_structure(self, tmp_path):
        """Test the structure of the generated report."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        report = generate_hygiene_report([test_file], "test-project")

        assert "project_id" in report
        assert report["project_id"] == "test-project"
        assert "timestamp" in report
        assert report["status"] == "success"
        assert "files" in report
        assert "aggregate_hash" in report
        assert "total_files" in report
        assert report["total_files"] == 1

    def test_file_entry_details(self, tmp_path):
        """Test that file entries contain correct details."""
        test_file = tmp_path / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)

        report = generate_hygiene_report([test_file], "test-project")
        file_entry = report["files"][0]

        assert "path" in file_entry
        assert "size_bytes" in file_entry
        assert "sha256" in file_entry
        assert file_entry["size_bytes"] == len(content)
        assert file_entry["sha256"] == hashlib.sha256(content).hexdigest()

    def test_aggregate_hash_consistency(self, tmp_path):
        """Test that aggregate hash is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        report1 = generate_hygiene_report([test_file], "test-project")
        report2 = generate_hygiene_report([test_file], "test-project")

        assert report1["aggregate_hash"] == report2["aggregate_hash"]


class TestWriteHygieneReport:
    def test_write_valid_report(self, tmp_path):
        """Test writing a valid report to a file."""
        report = {
            "project_id": "test",
            "timestamp": "2023-01-01T00:00:00",
            "status": "success",
            "files": [],
            "aggregate_hash": "abc123",
            "total_files": 0
        }
        output_path = tmp_path / "hygiene.yaml"

        write_hygiene_report(report, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "project_id: test" in content
        assert "status: success" in content

    def test_create_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        report = {
            "project_id": "test",
            "timestamp": "2023-01-01T00:00:00",
            "status": "success",
            "files": [],
            "aggregate_hash": "abc123",
            "total_files": 0
        }
        output_path = tmp_path / "deep" / "nested" / "dir" / "hygiene.yaml"

        write_hygiene_report(report, output_path)

        assert output_path.exists()