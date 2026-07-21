"""
Unit tests for checksum generation functionality.
Tests for T031: Generate data/checksums.json including SHA-256 hashes.
"""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from generate_checksums import compute_file_hash, collect_files, generate_checksums


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_compute_hash_small_file(self, tmp_path):
        """Test hashing a small file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_hash(test_file)

        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length

    def test_compute_hash_large_file(self, tmp_path):
        """Test hashing a larger file to ensure chunked reading works."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"X" * (1024 * 1024)
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_hash(test_file)

        assert actual_hash == expected_hash

    def test_compute_hash_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_hash(nonexistent)


class TestCollectFiles:
    """Tests for collect_files function."""

    def test_collect_all_files(self, tmp_path):
        """Test collecting all files in a directory."""
        # Create test files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").touch()

        files = collect_files(tmp_path)

        assert len(files) == 3
        assert all(isinstance(f, Path) for f in files)

    def test_collect_excludes_gitkeep(self, tmp_path):
        """Test that .gitkeep files are excluded by default."""
        (tmp_path / "keep.gitkeep").touch()
        (tmp_path / "real.txt").touch()

        files = collect_files(tmp_path)

        assert len(files) == 1
        assert "keep.gitkeep" not in str(files[0])

    def test_collect_empty_directory(self, tmp_path):
        """Test collecting from empty directory."""
        files = collect_files(tmp_path)
        assert files == []

    def test_collect_with_custom_excludes(self, tmp_path):
        """Test collecting with custom exclude patterns."""
        (tmp_path / "file.txt").touch()
        (tmp_path / "backup.bak").touch()

        files = collect_files(tmp_path, exclude_patterns=[".bak"])

        assert len(files) == 1
        assert "file.txt" in str(files[0])


class TestGenerateChecksums:
    """Tests for generate_checksums function."""

    def test_generate_checksums_creates_output(self, tmp_path):
        """Test that checksums.json is created with correct structure."""
        # Create test directories and files
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        (raw_dir / "test.txt").write_text("test content")

        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "test.py").write_text("print('hello')")

        output_path = tmp_path / "data" / "checksums.json"

        checksums = generate_checksums(raw_dir, code_dir, output_path)

        # Verify output file exists
        assert output_path.exists()

        # Verify checksums dictionary structure
        assert isinstance(checksums, dict)
        assert len(checksums) >= 2  # At least test.txt and test.py

        # Verify all values are valid SHA-256 hashes
        for path, hash_value in checksums.items():
            assert len(hash_value) == 64
            assert all(c in '0123456789abcdef' for c in hash_value)

    def test_generate_checksums_invalidates_missing_dir(self, tmp_path):
        """Test that FileNotFoundError is raised for missing directory."""
        non_existent_dir = tmp_path / "non_existent"

        with pytest.raises(FileNotFoundError):
            generate_checksums(non_existent_dir, tmp_path, tmp_path / "out.json")

    def test_generate_checksums_json_format(self, tmp_path):
        """Test that output JSON is properly formatted."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        (raw_dir / "data.txt").write_text("data")

        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "module.py").write_text("code")

        output_path = tmp_path / "data" / "checksums.json"

        generate_checksums(raw_dir, code_dir, output_path)

        # Verify JSON is valid and parseable
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "data/raw/data.txt" in data or "data/data/raw/data.txt" in data
        assert "code/module.py" in data or "code/code/module.py" in data