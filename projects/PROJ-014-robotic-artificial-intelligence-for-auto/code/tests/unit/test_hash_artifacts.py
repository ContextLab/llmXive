"""
Unit tests for hash_artifacts.py script functionality.
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.hash_artifacts import compute_sha256, generate_hash_manifest


class TestComputeSha256:
    """Tests for the compute_sha256 function."""

    def test_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_bytes(b"")
        
        result = compute_sha256(file_path)
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_simple_content(self, tmp_path):
        """Test hashing a file with simple content."""
        file_path = tmp_path / "simple.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)
        
        result = compute_sha256(file_path)
        expected = hashlib.sha256(content).hexdigest()
        assert result == expected

    def test_large_file(self, tmp_path):
        """Test hashing a larger file to ensure chunking works."""
        file_path = tmp_path / "large.bin"
        # Create a 1MB file
        content = bytes(range(256)) * (1024 * 4)  # 1MB
        file_path.write_bytes(content)
        
        result = compute_sha256(file_path)
        expected = hashlib.sha256(content).hexdigest()
        assert result == expected

    def test_binary_content(self, tmp_path):
        """Test hashing binary content."""
        file_path = tmp_path / "binary.bin"
        content = bytes([0x00, 0xFF, 0x01, 0xFE, 0x80, 0x7F])
        file_path.write_bytes(content)
        
        result = compute_sha256(file_path)
        expected = hashlib.sha256(content).hexdigest()
        assert result == expected


class TestGenerateHashManifest:
    """Tests for the generate_hash_manifest function."""

    def test_creates_manifest_structure(self, tmp_path):
        """Test that manifest has correct top-level structure."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        output_path = tmp_path / "manifest.json"
        manifest = generate_hash_manifest(output_path)
        
        assert "generated_at" in manifest
        assert "project" in manifest
        assert "total_files" in manifest
        assert "artifacts" in manifest
        assert isinstance(manifest["artifacts"], dict)

    def test_includes_file_hash(self, tmp_path):
        """Test that manifest includes SHA-256 hash for files."""
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content)
        
        output_path = tmp_path / "manifest.json"
        manifest = generate_hash_manifest(output_path)
        
        # Find the test file in artifacts
        found = False
        for rel_path, info in manifest["artifacts"].items():
            if "test.txt" in rel_path:
                found = True
                assert "sha256" in info
                assert len(info["sha256"]) == 64  # SHA-256 hex length
                expected_hash = hashlib.sha256(content.encode()).hexdigest()
                assert info["sha256"] == expected_hash
                break
        
        assert found, "Test file not found in manifest"

    def test_includes_file_size(self, tmp_path):
        """Test that manifest includes file size."""
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content)
        
        output_path = tmp_path / "manifest.json"
        manifest = generate_hash_manifest(output_path)
        
        # Find the test file in artifacts
        for rel_path, info in manifest["artifacts"].items():
            if "test.txt" in rel_path:
                assert "size_bytes" in info
                assert info["size_bytes"] == len(content.encode())
                break

    def test_writes_to_file(self, tmp_path):
        """Test that manifest is written to the specified output path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        output_path = tmp_path / "output_manifest.json"
        generate_hash_manifest(output_path)
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded = json.load(f)
        assert "artifacts" in loaded

    def test_deterministic_output(self, tmp_path):
        """Test that running twice produces same hashes (excluding timestamp)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        output_path1 = tmp_path / "manifest1.json"
        output_path2 = tmp_path / "manifest2.json"
        
        manifest1 = generate_hash_manifest(output_path1)
        manifest2 = generate_hash_manifest(output_path2)
        
        # Compare artifacts (excluding timestamp)
        assert manifest1["artifacts"] == manifest2["artifacts"]
        assert manifest1["total_files"] == manifest2["total_files"]


class TestIntegration:
    """Integration tests for the hash generation workflow."""

    def test_empty_directory(self, tmp_path):
        """Test hashing when no matching files exist."""
        output_path = tmp_path / "manifest.json"
        manifest = generate_hash_manifest(output_path)
        
        assert manifest["total_files"] == 0
        assert manifest["artifacts"] == {}

    def test_mixed_file_types(self, tmp_path):
        """Test hashing multiple file types."""
        (tmp_path / "script.py").write_text("print('hello')")
        (tmp_path / "config.json").write_text('{"key": "value"}')
        (tmp_path / "readme.txt").write_text("Documentation")
        (tmp_path / "hidden.txt").write_text("hidden")
        
        output_path = tmp_path / "manifest.json"
        manifest = generate_hash_manifest(output_path)
        
        # Should include .py, .json, .txt but not hidden files
        assert manifest["total_files"] >= 3  # At least the three visible files
        
        # Verify all expected files are present
        paths = list(manifest["artifacts"].keys())
        assert any("script.py" in p for p in paths)
        assert any("config.json" in p for p in paths)
        assert any("readme.txt" in p for p in paths)