"""
Unit tests for manifest generation and validation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.src.utils.manifest import (
    compute_sha256,
    find_files_to_hash,
    generate_manifest,
    validate_manifest,
    main
)


class TestComputeSha256:
    def test_compute_sha256_known_file(self, tmp_path):
        """Test SHA256 computation for a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        hash_result = compute_sha256(test_file)
        
        # Known SHA256 for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_result == expected_hash
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA256 computation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        hash_result = compute_sha256(test_file)
        
        # Known SHA256 for empty file
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected_hash
    
    def test_compute_sha256_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)


class TestFindFilesToHash:
    def test_find_files_basic(self, tmp_path):
        """Test basic file discovery."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        files = find_files_to_hash(tmp_path)
        
        assert len(files) == 2
        assert all(f.name in ["file1.txt", "file2.txt"] for f in files)
    
    def test_find_files_recursive(self, tmp_path):
        """Test recursive file discovery."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")
        
        files = find_files_to_hash(tmp_path)
        
        assert len(files) == 2
    
    def test_find_files_excludes_pycache(self, tmp_path):
        """Test that __pycache__ is excluded."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (tmp_path / "file1.txt").write_text("content1")
        (pycache / "cache.pyc").write_text("cache")
        
        files = find_files_to_hash(tmp_path)
        
        assert len(files) == 1
        assert files[0].name == "file1.txt"
    
    def test_find_files_excludes_pyc(self, tmp_path):
        """Test that .pyc files are excluded."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.pyc").write_text("bytecode")
        
        files = find_files_to_hash(tmp_path)
        
        assert len(files) == 1
        assert files[0].name == "file1.txt"


class TestGenerateManifest:
    def test_generate_manifest_creates_file(self, tmp_path):
        """Test that generate_manifest creates the manifest file."""
        (tmp_path / "file1.txt").write_text("content1")
        
        manifest = generate_manifest(tmp_path)
        
        assert "generated_at" in manifest
        assert "files" in manifest
        assert "file1.txt" in manifest["files"]
        assert "sha256" in manifest["files"]["file1.txt"]
    
    def test_generate_manifest_with_multiple_files(self, tmp_path):
        """Test manifest generation with multiple files."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.json").write_text('{"key": "value"}')
        
        manifest = generate_manifest(tmp_path)
        
        assert len(manifest["files"]) == 2
        assert "file1.txt" in manifest["files"]
        assert "file2.json" in manifest["files"]
    
    def test_generate_manifest_writes_to_disk(self, tmp_path):
        """Test that manifest is written to disk."""
        (tmp_path / "file1.txt").write_text("content1")
        manifest_path = tmp_path / "manifest.json"
        
        generate_manifest(tmp_path, manifest_path)
        
        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            data = json.load(f)
        assert "files" in data
    
    def test_generate_manifest_empty_directory(self, tmp_path):
        """Test manifest generation for empty directory."""
        manifest = generate_manifest(tmp_path)
        
        assert len(manifest["files"]) == 0


class TestValidateManifest:
    def test_validate_manifest_valid(self, tmp_path):
        """Test validation of a valid manifest."""
        (tmp_path / "file1.txt").write_text("content1")
        
        # Generate manifest
        generate_manifest(tmp_path)
        manifest_path = tmp_path / "manifest.json"
        
        is_valid, errors = validate_manifest(manifest_path, tmp_path)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_manifest_missing_file(self, tmp_path):
        """Test validation when a file is missing."""
        (tmp_path / "file1.txt").write_text("content1")
        
        # Generate manifest
        generate_manifest(tmp_path)
        manifest_path = tmp_path / "manifest.json"
        
        # Remove the file
        (tmp_path / "file1.txt").unlink()
        
        is_valid, errors = validate_manifest(manifest_path, tmp_path)
        
        assert not is_valid
        assert len(errors) == 1
        assert "missing" in errors[0].lower()
    
    def test_validate_manifest_hash_mismatch(self, tmp_path):
        """Test validation when hash doesn't match."""
        (tmp_path / "file1.txt").write_text("content1")
        
        # Generate manifest
        generate_manifest(tmp_path)
        
        # Modify the file
        (tmp_path / "file1.txt").write_text("modified content")
        
        manifest_path = tmp_path / "manifest.json"
        is_valid, errors = validate_manifest(manifest_path, tmp_path)
        
        assert not is_valid
        assert len(errors) == 1
        assert "mismatch" in errors[0].lower()
    
    def test_validate_manifest_missing_manifest_file(self, tmp_path):
        """Test validation when manifest file is missing."""
        is_valid, errors = validate_manifest(tmp_path / "nonexistent.json", tmp_path)
        
        assert not is_valid
        assert len(errors) == 1
        assert "not found" in errors[0].lower()


class TestMain:
    def test_main_generate(self, tmp_path):
        """Test main function with generate action."""
        (tmp_path / "file1.txt").write_text("content1")
        
        import sys
        original_argv = sys.argv
        sys.argv = ["test", "generate", "--output-dir", str(tmp_path)]
        
        try:
            result = main()
            assert result == 0
        finally:
            sys.argv = original_argv
    
    def test_main_validate(self, tmp_path):
        """Test main function with validate action."""
        (tmp_path / "file1.txt").write_text("content1")
        generate_manifest(tmp_path)
        
        import sys
        original_argv = sys.argv
        sys.argv = ["test", "validate", "--output-dir", str(tmp_path)]
        
        try:
            result = main()
            assert result == 0
        finally:
            sys.argv = original_argv
    
    def test_main_validate_failure(self, tmp_path):
        """Test main function with validate action when validation fails."""
        (tmp_path / "file1.txt").write_text("content1")
        generate_manifest(tmp_path)
        
        # Modify file to cause hash mismatch
        (tmp_path / "file1.txt").write_text("modified")
        
        import sys
        original_argv = sys.argv
        sys.argv = ["test", "validate", "--output-dir", str(tmp_path)]
        
        try:
            result = main()
            assert result == 1
        finally:
            sys.argv = original_argv
