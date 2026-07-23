"""
Unit tests for utils/hasher.py
Tests Constitution Principle V: Versioning and Traceability.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.hasher import compute_file_hash, hash_directory, generate_artifact_manifest


class TestComputeFileHash:
    """Tests for the compute_file_hash function."""
    
    def test_compute_hash_simple_file(self, tmp_path):
        """Test hashing a simple text file."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        actual_hash = compute_file_hash(test_file)
        
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length
        
    def test_compute_hash_binary_file(self, tmp_path):
        """Test hashing a binary file."""
        test_file = tmp_path / "binary.bin"
        content = b"\x00\x01\x02\x03\xff\xfe\xfd"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_hash(test_file)
        
        assert actual_hash == expected_hash
        
    def test_compute_hash_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_file_hash(test_file)
        
        assert actual_hash == expected_hash
        
    def test_compute_hash_nonexistent_file(self, tmp_path):
        """Test that hashing a non-existent file raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_hash(nonexistent)
        
    def test_compute_hash_large_file(self, tmp_path):
        """Test hashing a larger file to ensure chunked reading works."""
        test_file = tmp_path / "large.txt"
        content = "x" * (1024 * 1024)  # 1 MB
        test_file.write_text(content)
        
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        actual_hash = compute_file_hash(test_file)
        
        assert actual_hash == expected_hash


class TestHashDirectory:
    """Tests for the hash_directory function."""
    
    def test_hash_directory_single_file(self, tmp_path):
        """Test hashing a directory with a single file."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 1
        assert "file.txt" in hashes
        assert len(hashes["file.txt"]) == 64
        
    def test_hash_directory_multiple_files(self, tmp_path):
        """Test hashing a directory with multiple files."""
        (tmp_path / "a.txt").write_text("content_a")
        (tmp_path / "b.txt").write_text("content_b")
        (tmp_path / "c.txt").write_text("content_c")
        
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 3
        assert "a.txt" in hashes
        assert "b.txt" in hashes
        assert "c.txt" in hashes
        
    def test_hash_directory_empty(self, tmp_path):
        """Test hashing an empty directory."""
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 0
        
    def test_hash_directory_ignores_subdirs(self, tmp_path):
        """Test that subdirectories are ignored (non-recursive)."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")
        (tmp_path / "root.txt").write_text("root")
        
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 1
        assert "root.txt" in hashes
        assert "subdir" not in hashes
        assert "subdir/nested.txt" not in hashes
        
    def test_hash_directory_nonexistent(self):
        """Test that hashing a non-existent directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            hash_directory(Path("/nonexistent/path"))
        
    def test_hash_directory_not_a_dir(self, tmp_path):
        """Test that hashing a file (not directory) raises NotADirectoryError."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        
        with pytest.raises(NotADirectoryError):
            hash_directory(test_file)


class TestGenerateArtifactManifest:
    """Tests for the generate_artifact_manifest function."""
    
    def test_generate_manifest_creates_file(self, tmp_path):
        """Test that manifest file is created."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_artifact_manifest(tmp_path, output_path)
        
        assert output_path.exists()
        assert manifest["file_count"] == 1
        
    def test_generate_manifest_structure(self, tmp_path):
        """Test manifest has correct structure."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_artifact_manifest(tmp_path, output_path)
        
        assert "version" in manifest
        assert "generated_at" in manifest
        assert "input_directory" in manifest
        assert "file_count" in manifest
        assert "artifacts" in manifest
        
    def test_generate_manifest_content(self, tmp_path):
        """Test manifest contains correct file information."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_artifact_manifest(tmp_path, output_path)
        
        assert "test.txt" in manifest["artifacts"]
        assert "hash" in manifest["artifacts"]["test.txt"]
        assert len(manifest["artifacts"]["test.txt"]["hash"]) == 64
        
    def test_generate_manifest_with_metadata(self, tmp_path):
        """Test manifest includes metadata when requested."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_artifact_manifest(tmp_path, output_path, include_metadata=True)
        
        artifact = manifest["artifacts"]["test.txt"]
        assert "size_bytes" in artifact
        assert "modified_at" in artifact
        
    def test_generate_manifest_without_metadata(self, tmp_path):
        """Test manifest excludes metadata when requested."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_artifact_manifest(tmp_path, output_path, include_metadata=False)
        
        artifact = manifest["artifacts"]["test.txt"]
        assert "size_bytes" not in artifact
        assert "modified_at" not in artifact
        
    def test_generate_manifest_output_valid_yaml(self, tmp_path):
        """Test that output file is valid YAML."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "manifest.yaml"
        
        generate_artifact_manifest(tmp_path, output_path)
        
        # Should not raise
        with open(output_path, "r") as f:
            loaded = yaml.safe_load(f)
        
        assert loaded is not None
        assert "artifacts" in loaded
        
    def test_generate_manifest_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created for output."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        output_path = tmp_path / "subdir" / "manifest.yaml"
        
        manifest = generate_artifact_manifest(tmp_path, output_path)
        
        assert output_path.exists()
        assert manifest["file_count"] == 1