"""
Unit tests for the checksum verification logic (T050).
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.verify_checksums import compute_sha256, load_hash_registry, verify_artifact

class TestComputeSha256:
    def test_compute_sha256_valid_file(self, tmp_path):
        """Test computing SHA-256 of a valid file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, world!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test computing SHA-256 of an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash

    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test computing SHA-256 of a non-existent file."""
        test_file = tmp_path / "nonexistent.txt"
        
        actual_hash = compute_sha256(test_file)
        assert actual_hash == ""

class TestLoadHashRegistry:
    def test_load_valid_registry(self, tmp_path):
        """Test loading a valid hash registry."""
        registry_file = tmp_path / "registry.json"
        data = {"hashes": {"file1.txt": "abc123", "file2.txt": "def456"}}
        registry_file.write_text(json.dumps(data))
        
        result = load_hash_registry(registry_file)
        assert result == data["hashes"]

    def test_load_nested_registry(self, tmp_path):
        """Test loading a nested hash registry."""
        registry_file = tmp_path / "registry.json"
        data = {"hashes": {"file1.txt": "abc123"}}
        registry_file.write_text(json.dumps(data))
        
        result = load_hash_registry(registry_file)
        assert result == data["hashes"]

    def test_load_empty_registry(self, tmp_path):
        """Test loading an empty registry."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text("{}")
        
        result = load_hash_registry(registry_file)
        assert result == {}

    def test_load_missing_registry(self, tmp_path):
        """Test loading a non-existent registry."""
        registry_file = tmp_path / "nonexistent.json"
        
        result = load_hash_registry(registry_file)
        assert result == {}

class TestVerifyArtifact:
    def test_verify_success(self, tmp_path):
        """Test successful verification."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()
        
        registry = {"test.txt": expected_hash}
        is_valid, message, _ = verify_artifact(test_file, expected_hash, registry)
        
        assert is_valid is True
        assert "OK" in message

    def test_verify_mismatch(self, tmp_path):
        """Test verification with hash mismatch."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        wrong_hash = "wrong_hash_value"
        
        registry = {"test.txt": wrong_hash}
        is_valid, message, actual_hash = verify_artifact(test_file, wrong_hash, registry)
        
        assert is_valid is False
        assert "MISMATCH" in message
        assert actual_hash == hashlib.sha256(content).hexdigest()

    def test_verify_missing_file(self, tmp_path):
        """Test verification of a missing file."""
        test_file = tmp_path / "nonexistent.txt"
        registry = {"nonexistent.txt": "some_hash"}
        
        is_valid, message, _ = verify_artifact(test_file, "some_hash", registry)
        
        assert is_valid is False
        assert "MISSING" in message