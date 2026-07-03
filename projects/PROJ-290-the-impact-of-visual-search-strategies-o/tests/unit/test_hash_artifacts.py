"""
Unit tests for hash_artifacts.py
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.utils.hash_artifacts import calculate_sha256, scan_directory, hash_artifacts


class TestCalculateSha256:
    def test_calculate_sha256_known_file(self, tmp_path):
        """Test hashing a file with known content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash

    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash


class TestScanDirectory:
    def test_scan_directory_all_files(self, tmp_path):
        """Test scanning directory for all files."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").touch()
        
        files = scan_directory(tmp_path)
        
        assert len(files) == 3
        assert all(f.suffix in [".txt", ".py"] for f in files)

    def test_scan_directory_extension_filter(self, tmp_path):
        """Test scanning directory with extension filter."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        
        files = scan_directory(tmp_path, extensions=[".py"])
        
        assert len(files) == 1
        assert files[0].suffix == ".py"

    def test_scan_directory_nonexistent(self, tmp_path):
        """Test scanning a non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        
        files = scan_directory(nonexistent)
        
        assert len(files) == 0


class TestHashArtifacts:
    def test_hash_artifacts_creates_manifest(self, tmp_path):
        """Test that hash_artifacts creates a valid manifest."""
        # Setup test directories
        data_dir = tmp_path / "data"
        code_dir = tmp_path / "code"
        state_dir = tmp_path / "state"
        data_dir.mkdir()
        code_dir.mkdir()
        state_dir.mkdir()
        
        # Create test files
        (data_dir / "data.csv").write_text("col1,col2\n1,2")
        (code_dir / "script.py").write_text("print('hello')")
        
        output_file = state_dir / "manifest.json"
        
        # Run function
        manifest = hash_artifacts(data_dir, code_dir, output_file)
        
        # Verify manifest structure
        assert "version" in manifest
        assert "paths" in manifest
        assert "summary" in manifest
        assert "data" in manifest["paths"]
        assert "code" in manifest["paths"]
        
        # Verify file counts
        assert manifest["summary"]["data_files"] == 1
        assert manifest["summary"]["code_files"] == 1
        assert manifest["summary"]["total_files"] == 2
        
        # Verify file exists on disk
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file) as f:
            saved_manifest = json.load(f)
        
        assert saved_manifest["paths"]["data"]
        assert saved_manifest["paths"]["code"]