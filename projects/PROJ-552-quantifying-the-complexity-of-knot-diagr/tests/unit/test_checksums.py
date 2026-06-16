"""
Unit tests for checksum generation module.

Tests verify SHA-256 checksum computation, file discovery, and output generation
per FR-007 reproducibility requirements.
"""

import pytest
import json
import csv
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from reproducibility.checksums import (
    ChecksumEntry,
    ChecksumRecord,
    compute_sha256,
    get_file_size,
    find_data_files,
    record_checksums,
    write_checksums_json,
    write_checksums_csv,
    write_checksums_documentation,
    main
)


class TestChecksumEntry:
    """Tests for ChecksumEntry dataclass."""

    def test_checksum_entry_creation(self):
        """Test ChecksumEntry can be created with required fields."""
        entry = ChecksumEntry(
            file_path="data/test.json",
            file_name="test.json",
            file_size_bytes=1024,
            sha256_hash="abc123"
        )
        assert entry.file_path == "data/test.json"
        assert entry.file_name == "test.json"
        assert entry.file_size_bytes == 1024
        assert entry.sha256_hash == "abc123"
        assert entry.algorithm == "SHA-256"
        assert entry.generated_at != ""

    def test_checksum_entry_auto_timestamp(self):
        """Test that generated_at is auto-populated."""
        entry = ChecksumEntry(
            file_path="data/test.json",
            file_name="test.json",
            file_size_bytes=1024,
            sha256_hash="abc123"
        )
        assert entry.generated_at != ""


class TestChecksumRecord:
    """Tests for ChecksumRecord dataclass."""

    def test_checksum_record_to_dict(self):
        """Test ChecksumRecord serialization to dict."""
        entry = ChecksumEntry(
            file_path="data/test.json",
            file_name="test.json",
            file_size_bytes=1024,
            sha256_hash="abc123"
        )
        record = ChecksumRecord(
            entries=[entry],
            total_files=1,
            total_size_bytes=1024,
            generated_at="2024-01-01T00:00:00",
            project_root="/test"
        )
        d = record.to_dict()
        assert "checksums" in d
        assert d["total_files"] == 1
        assert d["total_size_bytes"] == 1024
        assert d["algorithm"] == "SHA-256"


class TestComputeSha256:
    """Tests for SHA-256 computation."""

    def test_compute_sha256_known_hash(self, tmp_path):
        """Test SHA-256 computation on file with known content."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Compute hash
        computed_hash = compute_sha256(test_file)

        # Verify against expected hash
        expected_hash = hashlib.sha256(content).hexdigest()
        assert computed_hash == expected_hash

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation on empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        computed_hash = compute_sha256(test_file)
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert computed_hash == expected_hash

    def test_compute_sha256_large_file(self, tmp_path):
        """Test SHA-256 computation on larger file (tests chunking)."""
        test_file = tmp_path / "large.txt"
        # Create a file larger than 8KB chunk size
        content = b"X" * 100000
        test_file.write_bytes(content)

        computed_hash = compute_sha256(test_file)
        expected_hash = hashlib.sha256(content).hexdigest()
        assert computed_hash == expected_hash


class TestGetFileSize:
    """Tests for file size computation."""

    def test_get_file_size(self, tmp_path):
        """Test file size computation."""
        test_file = tmp_path / "test.txt"
        content = b"Hello"
        test_file.write_bytes(content)

        size = get_file_size(test_file)
        assert size == len(content)


class TestFindDataFiles:
    """Tests for data file discovery."""

    def test_find_data_files_all_extensions(self, tmp_path):
        """Test finding files with all supported extensions."""
        # Create files with different extensions
        (tmp_path / "test.json").write_text("{}")
        (tmp_path / "test.csv").write_text("a,b\n1,2")
        (tmp_path / "test.txt").write_text("text")
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "test.yaml").write_text("key: value")
        (tmp_path / "test.yml").write_text("key: value")
        (tmp_path / "test.png").write_bytes(b"png_data")

        files = find_data_files(tmp_path)
        assert len(files) == 6

    def test_find_data_files_subdirectories(self, tmp_path):
        """Test finding files in subdirectories."""
        subdir = tmp_path / "raw"
        subdir.mkdir()
        (subdir / "test.json").write_text("{}")

        files = find_data_files(tmp_path)
        assert len(files) == 1
        assert "raw/test.json" in str(files[0])

    def test_find_data_files_empty_directory(self, tmp_path):
        """Test finding files in empty directory."""
        files = find_data_files(tmp_path)
        assert len(files) == 0

    def test_find_data_files_nonexistent_directory(self, tmp_path):
        """Test finding files in non-existent directory."""
        files = find_data_files(tmp_path / "nonexistent")
        assert len(files) == 0


class TestRecordChecksums:
    """Tests for checksum recording."""

    def test_record_checksums_success(self, tmp_path):
        """Test successful checksum recording."""
        # Create test files
        (tmp_path / "test1.json").write_text("{}", encoding="utf-8")
        (tmp_path / "test2.csv").write_text("a,b\n1,2", encoding="utf-8")

        record = record_checksums(tmp_path, tmp_path)

        assert record.total_files == 2
        assert len(record.entries) == 2
        assert record.total_size_bytes > 0

    def test_record_checksums_hash_validity(self, tmp_path):
        """Test that recorded hashes are valid SHA-256."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}", encoding="utf-8")

        record = record_checksums(tmp_path, tmp_path)

        # SHA-256 produces 64 hex characters
        assert len(record.entries[0].sha256_hash) == 64
        # All characters should be hex
        assert all(c in "0123456789abcdef" for c in record.entries[0].sha256_hash)


class TestWriteChecksumsJson:
    """Tests for JSON output."""

    def test_write_checksums_json(self, tmp_path):
        """Test JSON output generation."""
        entry = ChecksumEntry(
            file_path="data/test.json",
            file_name="test.json",
            file_size_bytes=1024,
            sha256_hash="abc123"
        )
        record = ChecksumRecord(
            entries=[entry],
            total_files=1,
            total_size_bytes=1024,
            generated_at="2024-01-01T00:00:00",
            project_root="/test"
        )

        output_path = tmp_path / "checksums.json"
        write_checksums_json(record, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert "checksums" in data
        assert len(data["checksums"]) == 1


class TestWriteChecksumsCsv:
    """Tests for CSV output."""

    def test_write_checksums_csv(self, tmp_path):
        """Test CSV output generation."""
        entry = ChecksumEntry(
            file_path="data/test.json",
            file_name="test.json",
            file_size_bytes=1024,
            sha256_hash="abc123"
        )
        record = ChecksumRecord(
            entries=[entry],
            total_files=1,
            total_size_bytes=1024,
            generated_at="2024-01-01T00:00:00",
            project_root="/test"
        )

        output_path = tmp_path / "checksums.csv"
        write_checksums_csv(record, output_path)

        assert output_path.exists()
        with open(output_path, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2  # Header + 1 data row
        assert rows[0] == ["file_path", "file_name", "file_size_bytes", "sha256_hash", "algorithm", "generated_at"]


class TestWriteChecksumsDocumentation:
    """Tests for Markdown documentation output."""

    def test_write_checksums_documentation(self, tmp_path):
        """Test Markdown documentation generation."""
        entry = ChecksumEntry(
            file_path="data/test.json",
            file_name="test.json",
            file_size_bytes=1024,
            sha256_hash="abc123"
        )
        record = ChecksumRecord(
            entries=[entry],
            total_files=1,
            total_size_bytes=1024,
            generated_at="2024-01-01T00:00:00",
            project_root="/test"
        )

        output_path = tmp_path / "checksums.md"
        write_checksums_documentation(record, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Data File Checksums" in content
        assert "SHA-256" in content
        assert "abc123" in content


class TestMain:
    """Tests for main entry point."""

    def test_main_success(self, tmp_path):
        """Test successful main execution."""
        # Create data directory with test files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "test.json").write_text("{}", encoding="utf-8")

        # Mock project root
        with patch("pathlib.Path.__truediv__", side_effect=lambda self, other: tmp_path / other if other != "data" else data_dir):
            result = main()

        # Should complete successfully
        assert result == 0

    def test_main_no_data_directory(self, tmp_path):
        """Test main with non-existent data directory."""
        with patch("pathlib.Path.__truediv__", return_value=tmp_path / "nonexistent"):
            result = main()

        assert result == 1

    def test_main_empty_data_directory(self, tmp_path):
        """Test main with empty data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        with patch("pathlib.Path.__truediv__", side_effect=lambda self, other: data_dir if other == "data" else tmp_path / other):
            result = main()

        # Should complete successfully even with no files
        assert result == 0