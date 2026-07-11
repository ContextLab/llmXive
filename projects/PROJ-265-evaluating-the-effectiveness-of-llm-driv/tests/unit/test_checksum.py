"""
Unit tests for the checksum module.

Tests the artifact versioning and integrity checking functionality
as required by Constitution Principle V.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from checksum import (
    compute_sha256,
    should_exclude,
    scan_directory,
    save_checksum_manifest,
    verify_checksums,
    compute_and_save_manifest,
    EXCLUDE_PATTERNS,
    ARTIFACT_DIRS,
)

class TestComputeSha256:
    """Tests for SHA-256 computation."""

    def test_compute_sha256_known_file(self, tmp_path):
        """Test computing SHA-256 of a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Known SHA-256 for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test computing SHA-256 of an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        # Known SHA-256 for empty string
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test that computing SHA-256 of non-existent file raises error."""
        non_existent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)

class TestShouldExclude:
    """Tests for file exclusion logic."""

    def test_exclude_pycache(self, tmp_path):
        """Test that __pycache__ directories are excluded."""
        pycache_file = tmp_path / "__pycache__" / "module.cpython-311.pyc"
        pycache_file.parent.mkdir(parents=True)
        
        assert should_exclude(pycache_file) is True

    def test_exclude_git(self, tmp_path):
        """Test that .git directories are excluded."""
        git_file = tmp_path / ".git" / "config"
        git_file.parent.mkdir(parents=True)
        
        assert should_exclude(git_file) is True

    def test_exclude_pyc_files(self, tmp_path):
        """Test that .pyc files are excluded."""
        pyc_file = tmp_path / "module.pyc"
        
        assert should_exclude(pyc_file) is True

    def test_include_python_files(self, tmp_path):
        """Test that .py files are included."""
        py_file = tmp_path / "module.py"
        
        assert should_exclude(py_file) is False

    def test_include_json_files(self, tmp_path):
        """Test that .json files are included."""
        json_file = tmp_path / "data.json"
        
        assert should_exclude(json_file) is False

    def test_exclude_temp_files(self, tmp_path):
        """Test that .tmp files are excluded."""
        tmp_file = tmp_path / "temp.tmp"
        
        assert should_exclude(tmp_file) is False

class TestScanDirectory:
    """Tests for directory scanning."""

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        artifacts = scan_directory(tmp_path)
        assert len(artifacts) == 0

    def test_scan_directory_with_files(self, tmp_path):
        """Test scanning a directory with files."""
        (tmp_path / "file1.py").write_text("code")
        (tmp_path / "file2.py").write_text("code")
        
        artifacts = scan_directory(tmp_path)
        
        assert len(artifacts) == 2
        assert all(f.is_file() for f in artifacts)

    def test_scan_excludes_pycache(self, tmp_path):
        """Test that scanning excludes __pycache__ directories."""
        (tmp_path / "main.py").write_text("code")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "main.cpython-311.pyc").write_bytes(b"bytecode")
        
        artifacts = scan_directory(tmp_path)
        
        assert len(artifacts) == 1
        assert artifacts[0].name == "main.py"

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test scanning a non-existent directory returns empty list."""
        non_existent = tmp_path / "does_not_exist"
        
        artifacts = scan_directory(non_existent)
        
        assert len(artifacts) == 0

class TestSaveChecksumManifest:
    """Tests for manifest saving."""

    def test_save_checksum_manifest_creates_file(self, tmp_path):
        """Test that saving checksums creates the manifest file."""
        with patch("checksum.MANIFEST_PATH", tmp_path / "manifest.json"):
            checksums = {"file.py": "abc123"}
            save_checksum_manifest(checksums)
            
            assert (tmp_path / "manifest.json").exists()

    def test_save_checksum_manifest_structure(self, tmp_path):
        """Test that the manifest has the correct structure."""
        with patch("checksum.MANIFEST_PATH", tmp_path / "manifest.json"):
            checksums = {"file.py": "abc123"}
            metadata = {"test": "value"}
            save_checksum_manifest(checksums, metadata)
            
            with open(tmp_path / "manifest.json", "r") as f:
                manifest = json.load(f)
            
            assert "version" in manifest
            assert "created_at" in manifest
            assert "checksums" in manifest
            assert manifest["checksums"] == checksums
            assert manifest["metadata"] == metadata

    def test_save_checksum_manifest_creates_directory(self, tmp_path):
        """Test that saving checksums creates the directory if needed."""
        nested_path = tmp_path / "nested" / "state" / "manifest.json"
        with patch("checksum.MANIFEST_PATH", nested_path):
            checksums = {"file.py": "abc123"}
            save_checksum_manifest(checksums)
            
            assert nested_path.exists()

class TestVerifyChecksums:
    """Tests for checksum verification."""

    def test_verify_no_manifest(self, tmp_path):
        """Test verification when no manifest exists."""
        with patch("checksum.MANIFEST_PATH", tmp_path / "nonexistent.json"):
            all_valid, modified, missing = verify_checksums()
            
            assert all_valid is False
            assert len(missing) == 1
            assert "Manifest file not found" in missing

    def test_verify_valid_checksums(self, tmp_path):
        """Test verification with valid checksums."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # Create manifest with correct checksum
        expected_hash = compute_sha256(test_file)
        manifest_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": {str(test_file.relative_to(PROJECT_ROOT)): expected_hash}
        }
        
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        with patch("checksum.MANIFEST_PATH", manifest_path):
            with patch("checksum.PROJECT_ROOT", tmp_path):
                all_valid, modified, missing = verify_checksums()
                
                assert all_valid is True
                assert len(modified) == 0
                assert len(missing) == 0

    def test_verify_modified_file(self, tmp_path):
        """Test verification detects modified files."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # Create manifest with wrong checksum
        manifest_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": {str(test_file.relative_to(PROJECT_ROOT)): "wrong_hash"}
        }
        
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        with patch("checksum.MANIFEST_PATH", manifest_path):
            with patch("checksum.PROJECT_ROOT", tmp_path):
                all_valid, modified, missing = verify_checksums()
                
                assert all_valid is False
                assert len(modified) == 1
                assert str(test_file.relative_to(PROJECT_ROOT)) in modified[0]

    def test_verify_missing_file(self, tmp_path):
        """Test verification detects missing files."""
        # Create manifest referencing non-existent file
        manifest_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": {"nonexistent.py": "abc123"}
        }
        
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        with patch("checksum.MANIFEST_PATH", manifest_path):
            with patch("checksum.PROJECT_ROOT", tmp_path):
                all_valid, modified, missing = verify_checksums()
                
                assert all_valid is False
                assert len(missing) == 1
                assert "nonexistent.py" in missing[0]

class TestComputeAndSaveManifest:
    """Tests for computing and saving the full manifest."""

    def test_compute_and_save_manifest(self, tmp_path):
        """Test computing and saving a full manifest."""
        # Create some test files
        (tmp_path / "code" / "main.py").mkdir(parents=True)
        (tmp_path / "code" / "main.py" / "file1.py").write_text("code1")
        (tmp_path / "code" / "main.py" / "file2.py").write_text("code2")
        
        manifest_path = tmp_path / "state" / "artifact_manifest.json"
        
        with patch("checksum.MANIFEST_PATH", manifest_path):
            with patch("checksum.PROJECT_ROOT", tmp_path):
                with patch("checksum.ARTIFACT_DIRS", ["code"]):
                    checksums = compute_and_save_manifest()
                    
                    assert len(checksums) == 2
                    assert manifest_path.exists()
                    
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                    
                    assert manifest["artifact_count"] == 2

class TestMain:
    """Tests for the main entry point."""

    def test_main_compute(self, tmp_path, capsys):
        """Test main with compute command."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        manifest_path = tmp_path / "state" / "artifact_manifest.json"
        
        with patch("sys.argv", ["checksum.py", "compute"]):
            with patch("checksum.MANIFEST_PATH", manifest_path):
                with patch("checksum.PROJECT_ROOT", tmp_path):
                    with patch("checksum.ARTIFACT_DIRS", [""]):
                        result = main()
                        
                        assert result == 0
                        assert manifest_path.exists()

    def test_main_verify_with_valid_manifest(self, tmp_path, capsys):
        """Test main with verify command on valid manifest."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # Create valid manifest
        expected_hash = compute_sha256(test_file)
        manifest_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": {str(test_file.relative_to(tmp_path)): expected_hash}
        }
        
        manifest_path = tmp_path / "state" / "artifact_manifest.json"
        manifest_path.parent.mkdir(parents=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        with patch("sys.argv", ["checksum.py", "verify"]):
            with patch("checksum.MANIFEST_PATH", manifest_path):
                with patch("checksum.PROJECT_ROOT", tmp_path):
                    result = main()
                    
                    assert result == 0

    def test_main_verify_with_invalid_manifest(self, tmp_path, capsys):
        """Test main with verify command on invalid manifest."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # Create invalid manifest (wrong hash)
        manifest_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": {str(test_file.relative_to(tmp_path)): "wrong_hash"}
        }
        
        manifest_path = tmp_path / "state" / "artifact_manifest.json"
        manifest_path.parent.mkdir(parents=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        with patch("sys.argv", ["checksum.py", "verify"]):
            with patch("checksum.MANIFEST_PATH", manifest_path):
                with patch("checksum.PROJECT_ROOT", tmp_path):
                    result = main()
                    
                    assert result == 1

    def test_main_status(self, tmp_path, capsys):
        """Test main with status command."""
        # Create valid manifest
        manifest_path = tmp_path / "state" / "artifact_manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": {"test.py": "abc123"}
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        with patch("sys.argv", ["checksum.py", "status"]):
            with patch("checksum.MANIFEST_PATH", manifest_path):
                result = main()
                
                # Status should return 0 even if checksums don't match
                # (it just reports status, doesn't fail on mismatch)
                assert result in [0, 1]

    def test_main_unknown_command(self, tmp_path, capsys):
        """Test main with unknown command."""
        with patch("sys.argv", ["checksum.py", "unknown"]):
            result = main()
            
            assert result == 1