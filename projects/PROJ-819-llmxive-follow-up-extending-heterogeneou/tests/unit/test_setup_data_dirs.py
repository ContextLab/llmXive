"""
Unit tests for setup_data_dirs.py (T011).

Tests verify:
1. Directory creation works correctly
2. SHA-256 checksum calculation is accurate
3. File discovery works recursively
4. Checksums are saved in correct format
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add the code directory to the path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import (
    calculate_sha256,
    ensure_directories,
    get_data_files,
    generate_checksums,
    save_checksums
)


class TestCalculateSha256:
    """Tests for SHA-256 calculation function."""

    def test_empty_file(self, tmp_path: Path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        hash_result = calculate_sha256(test_file)
        
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected

    def test_simple_content(self, tmp_path: Path):
        """Test hashing a file with simple content."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        hash_result = calculate_sha256(test_file)
        
        # Calculate expected hash
        expected = hashlib.sha256(content.encode('utf-8')).hexdigest()
        assert hash_result == expected

    def test_binary_content(self, tmp_path: Path):
        """Test hashing a file with binary content."""
        test_file = tmp_path / "binary.bin"
        binary_content = bytes(range(256))
        test_file.write_bytes(binary_content)
        
        hash_result = calculate_sha256(test_file)
        
        # Calculate expected hash
        expected = hashlib.sha256(binary_content).hexdigest()
        assert hash_result == expected


class TestEnsureDirectories:
    """Tests for directory creation function."""

    def test_creates_all_directories(self, tmp_path: Path):
        """Test that all required directories are created."""
        result = ensure_directories(tmp_path)
        
        assert "raw" in result
        assert "derived" in result
        assert "state_hashes" in result
        
        assert result["raw"].exists()
        assert result["derived"].exists()
        assert result["state_hashes"].exists()

    def test_uses_correct_paths(self, tmp_path: Path):
        """Test that directories are created at correct relative paths."""
        result = ensure_directories(tmp_path)
        
        assert result["raw"] == tmp_path / "data" / "raw"
        assert result["derived"] == tmp_path / "data" / "derived"
        assert result["state_hashes"] == tmp_path / "state" / "hashes"

    def test_idempotent(self, tmp_path: Path):
        """Test that calling twice doesn't cause errors."""
        first_result = ensure_directories(tmp_path)
        second_result = ensure_directories(tmp_path)
        
        assert first_result["raw"] == second_result["raw"]
        assert first_result["derived"] == second_result["derived"]
        assert first_result["state_hashes"] == second_result["state_hashes"]


class TestGetDataFiles:
    """Tests for file discovery function."""

    def test_empty_directory(self, tmp_path: Path):
        """Test discovering files in an empty directory."""
        result = get_data_files(tmp_path)
        assert result == []

    def test_single_file(self, tmp_path: Path):
        """Test discovering a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        result = get_data_files(tmp_path)
        assert len(result) == 1
        assert result[0] == test_file

    def test_recursive_discovery(self, tmp_path: Path):
        """Test discovering files in nested directories."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        file3 = subdir / "file3.txt"
        
        file1.write_text("1")
        file2.write_text("2")
        file3.write_text("3")
        
        result = get_data_files(tmp_path)
        
        assert len(result) == 3
        assert file1 in result
        assert file2 in result
        assert file3 in result

    def test_excludes_hidden_files(self, tmp_path: Path):
        """Test that hidden files are excluded."""
        visible_file = tmp_path / "visible.txt"
        hidden_file = tmp_path / ".hidden.txt"
        
        visible_file.write_text("visible")
        hidden_file.write_text("hidden")
        
        result = get_data_files(tmp_path)
        
        assert visible_file in result
        assert hidden_file not in result

    def test_excludes_manifest_files(self, tmp_path: Path):
        """Test that manifest.json files are excluded."""
        manifest_file = tmp_path / "manifest.json"
        other_file = tmp_path / "data.json"
        
        manifest_file.write_text("{}")
        other_file.write_text("{}")
        
        result = get_data_files(tmp_path)
        
        assert other_file in result
        assert manifest_file not in result


class TestGenerateChecksums:
    """Tests for checksum generation function."""

    def test_basic_checksum(self, tmp_path: Path):
        """Test basic checksum generation."""
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content)
        
        checksums = generate_checksums([test_file], tmp_path)
        
        assert len(checksums) == 1
        assert checksums[0]["path"] == "test.txt"
        assert checksums[0]["sha256"] == calculate_sha256(test_file)
        assert checksums[0]["size_bytes"] == len(content.encode('utf-8'))

    def test_multiple_files(self, tmp_path: Path):
        """Test checksum generation for multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("1")
        file2.write_text("2")
        
        checksums = generate_checksums([file1, file2], tmp_path)
        
        assert len(checksums) == 2
        paths = {c["path"] for c in checksums}
        assert "file1.txt" in paths
        assert "file2.txt" in paths

    def test_empty_file_list(self, tmp_path: Path):
        """Test checksum generation with empty file list."""
        checksums = generate_checksums([], tmp_path)
        assert checksums == []

    def test_nonexistent_file_handling(self, tmp_path: Path):
        """Test that non-existent files are handled gracefully."""
        nonexistent = tmp_path / "does_not_exist.txt"
        real_file = tmp_path / "real.txt"
        real_file.write_text("real")
        
        # Should not raise, just skip the nonexistent file
        checksums = generate_checksums([nonexistent, real_file], tmp_path)
        
        # Should only have the real file
        assert len(checksums) == 1
        assert checksums[0]["path"] == "real.txt"


class TestSaveChecksums:
    """Tests for saving checksums to file."""

    def test_creates_json_file(self, tmp_path: Path):
        """Test that the JSON file is created."""
        output_file = tmp_path / "checksums.json"
        checksums = [{"path": "test.txt", "sha256": "abc123"}]
        
        save_checksums(checksums, output_file)
        
        assert output_file.exists()

    def test_valid_json_structure(self, tmp_path: Path):
        """Test that the saved JSON has the correct structure."""
        output_file = tmp_path / "checksums.json"
        checksums = [{"path": "test.txt", "sha256": "abc123", "size_bytes": 10}]
        
        save_checksums(checksums, output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "files" in data
        assert "total_files" in data
        assert "generated_at" in data
        assert data["total_files"] == 1
        assert data["files"][0]["path"] == "test.txt"

    def test_creates_parent_directories(self, tmp_path: Path):
        """Test that parent directories are created if needed."""
        output_file = tmp_path / "nested" / "dir" / "checksums.json"
        checksums = [{"path": "test.txt", "sha256": "abc123"}]
        
        save_checksums(checksums, output_file)
        
        assert output_file.exists()

    def test_correct_checksum_count(self, tmp_path: Path):
        """Test that the correct number of checksums is saved."""
        output_file = tmp_path / "checksums.json"
        checksums = [
            {"path": f"file{i}.txt", "sha256": f"hash{i}"}
            for i in range(5)
        ]
        
        save_checksums(checksums, output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["total_files"] == 5
        assert len(data["files"]) == 5