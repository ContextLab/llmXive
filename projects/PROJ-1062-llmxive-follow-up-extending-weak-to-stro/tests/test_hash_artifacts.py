"""
Unit tests for hash_artifacts.py

Tests the SHA-256 hashing functionality and manifest generation.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import hashlib

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from scripts.hash_artifacts import (
    compute_sha256,
    should_exclude,
    scan_directory,
    generate_manifest,
    save_manifest,
    verify_artifacts
)


class TestComputeSha256:
    """Tests for compute_sha256 function"""

    def test_empty_file(self):
        """Test hashing an empty file"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"")
            temp_path = Path(f.name)

        try:
            hash_value = compute_sha256(temp_path)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert hash_value == expected
        finally:
            temp_path.unlink()

    def test_simple_text(self):
        """Test hashing a simple text file"""
        content = b"Hello, World!"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            hash_value = compute_sha256(temp_path)
            expected = hashlib.sha256(content).hexdigest()
            assert hash_value == expected
        finally:
            temp_path.unlink()

    def test_large_file(self):
        """Test hashing a larger file"""
        content = b"0" * 1000000  # 1MB of zeros
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            hash_value = compute_sha256(temp_path)
            expected = hashlib.sha256(content).hexdigest()
            assert hash_value == expected
        finally:
            temp_path.unlink()


class TestShouldExclude:
    """Tests for should_exclude function"""

    def test_exclude_gitkeep(self):
        """Test that .gitkeep files are excluded"""
        file_path = Path("/some/path/.gitkeep")
        assert should_exclude(file_path) is True

    def test_exclude_pycache(self):
        """Test that __pycache__ directories are excluded"""
        file_path = Path("/some/path/__pycache__/module.pyc")
        assert should_exclude(file_path) is True

    def test_exclude_pyc(self):
        """Test that .pyc files are excluded"""
        file_path = Path("/some/path/module.pyc")
        assert should_exclude(file_path) is True

    def test_include_regular_file(self):
        """Test that regular files are not excluded"""
        file_path = Path("/some/path/data.jsonl")
        assert should_exclude(file_path) is False

    def test_include_json_file(self):
        """Test that .json files are not excluded"""
        file_path = Path("/some/path/results.json")
        assert should_exclude(file_path) is False


class TestScanDirectory:
    """Tests for scan_directory function"""

    def test_scan_empty_directory(self):
        """Test scanning an empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files = scan_directory(temp_path)
            assert len(files) == 0

    def test_scan_directory_with_files(self):
        """Test scanning a directory with files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create some test files
            (temp_path / "file1.txt").write_text("content1")
            (temp_path / "file2.json").write_text("{}")
            (temp_path / ".gitkeep").write_text("")
            
            # Create a subdirectory with files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")
            (subdir / "file4.pyc").write_text("bytecode")
            
            files = scan_directory(temp_path)
            file_names = [f.name for f in files]
            
            # Should include regular files but exclude .gitkeep and .pyc
            assert "file1.txt" in file_names
            assert "file2.json" in file_names
            assert "file3.txt" in file_names
            assert ".gitkeep" not in file_names
            assert "file4.pyc" not in file_names

    def test_nonexistent_directory(self):
        """Test scanning a non-existent directory"""
        non_existent = Path("/non/existent/directory")
        files = scan_directory(non_existent)
        assert len(files) == 0


class TestSaveAndVerifyManifest:
    """Tests for save_manifest and verify_artifacts functions"""

    def test_save_and_verify_manifest(self):
        """Test saving and verifying a manifest"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.txt").write_text("content1")
            (temp_path / "file2.json").write_text('{"key": "value"}')
            
            # Create a mock manifest
            manifest = {
                "version": "1.0",
                "generated_at": "2024-01-01T00:00:00Z",
                "project_root": str(temp_path),
                "artifacts": [
                    {
                        "path": "file1.txt",
                        "sha256": compute_sha256(temp_path / "file1.txt"),
                        "size_bytes": 8,
                        "type": ".txt",
                        "directory": "."
                    },
                    {
                        "path": "file2.json",
                        "sha256": compute_sha256(temp_path / "file2.json"),
                        "size_bytes": 16,
                        "type": ".json",
                        "directory": "."
                    }
                ]
            }
            
            manifest_path = temp_path / "manifest.json"
            save_manifest(manifest, manifest_path)
            
            # Verify the manifest was saved
            assert manifest_path.exists()
            with open(manifest_path, "r") as f:
                saved_manifest = json.load(f)
            assert len(saved_manifest["artifacts"]) == 2
            
            # Verify artifacts
            all_valid, failed_files = verify_artifacts(manifest_path)
            assert all_valid is True
            assert len(failed_files) == 0

    def test_verify_modified_file(self):
        """Test verification fails when a file is modified"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file
            file_path = temp_path / "file1.txt"
            file_path.write_text("original content")
            
            # Create manifest with original hash
            original_hash = compute_sha256(file_path)
            manifest = {
                "version": "1.0",
                "generated_at": "2024-01-01T00:00:00Z",
                "project_root": str(temp_path),
                "artifacts": [
                    {
                        "path": "file1.txt",
                        "sha256": original_hash,
                        "size_bytes": 16,
                        "type": ".txt",
                        "directory": "."
                    }
                ]
            }
            
            manifest_path = temp_path / "manifest.json"
            save_manifest(manifest, manifest_path)
            
            # Modify the file
            file_path.write_text("modified content")
            
            # Verification should fail
            all_valid, failed_files = verify_artifacts(manifest_path)
            assert all_valid is False
            assert len(failed_files) == 1
            assert "Hash mismatch" in failed_files[0]

    def test_verify_missing_file(self):
        """Test verification fails when a file is missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create manifest referencing a non-existent file
            manifest = {
                "version": "1.0",
                "generated_at": "2024-01-01T00:00:00Z",
                "project_root": str(temp_path),
                "artifacts": [
                    {
                        "path": "missing_file.txt",
                        "sha256": "abc123",
                        "size_bytes": 10,
                        "type": ".txt",
                        "directory": "."
                    }
                ]
            }
            
            manifest_path = temp_path / "manifest.json"
            save_manifest(manifest, manifest_path)
            
            # Verification should fail
            all_valid, failed_files = verify_artifacts(manifest_path)
            assert all_valid is False
            assert len(failed_files) == 1
            assert "Missing" in failed_files[0]