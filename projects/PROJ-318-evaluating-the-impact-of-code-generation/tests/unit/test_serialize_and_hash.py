"""
Unit tests for T019: serialize_and_hash.py
"""
import json
import os
import tempfile
import shutil
import yaml
from pathlib import Path
import pytest

# Adjust path for local testing if run directly
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.serialize_and_hash import (
    compute_sha256,
    validate_ast_params,
    ensure_state_file,
    update_state_file
)
from code.utils.exceptions import SerializationException

class TestComputeSha256:
    def test_compute_sha256_known_value(self, tmp_path):
        """Test SHA-256 computation against a known string."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        # Expected hash for "Hello, World!"
        expected_hash = "7f83b1657ff1fc53b92dc18148a1d65dfa355894746b7c0939c6372069e94600"
        
        result = compute_sha256(test_file)
        assert result == expected_hash

    def test_compute_sha256_binary(self, tmp_path):
        """Test SHA-256 with binary content."""
        test_file = tmp_path / "test.bin"
        content = b"\x00\x01\x02\x03"
        test_file.write_bytes(content)
        
        # Expected hash for b"\x00\x01\x02\x03"
        expected_hash = "a3c65c2974270fd093ee8a9bf8f7d36f15f21104943564949494949494949494" # Placeholder, calculate real one if needed, but logic holds
        # Let's calculate real one for safety in test
        import hashlib
        real_hash = hashlib.sha256(content).hexdigest()
        
        result = compute_sha256(test_file)
        assert result == real_hash

class TestValidateAstParams:
    def test_valid_list_with_params(self, tmp_path):
        """Test validation of a list containing records with ast_params."""
        test_file = tmp_path / "valid.json"
        data = [
            {"method": "foo", "ast_params": ["a", "b"]},
            {"method": "bar", "ast_params": []}
        ]
        test_file.write_text(json.dumps(data))
        
        assert validate_ast_params(test_file) is True

    def test_missing_ast_params(self, tmp_path):
        """Test validation failure when ast_params is missing."""
        test_file = tmp_path / "invalid.json"
        data = [
            {"method": "foo", "params": ["a"]} # Key is 'params', not 'ast_params'
        ]
        test_file.write_text(json.dumps(data))
        
        assert validate_ast_params(test_file) is False

    def test_non_list_ast_params(self, tmp_path):
        """Test validation failure when ast_params is not a list."""
        test_file = tmp_path / "invalid.json"
        data = [
            {"method": "foo", "ast_params": "not a list"}
        ]
        test_file.write_text(json.dumps(data))
        
        assert validate_ast_params(test_file) is False

    def test_invalid_json(self, tmp_path):
        """Test exception raising for invalid JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")
        
        with pytest.raises(SerializationException):
            validate_ast_params(test_file)

class TestEnsureStateFile:
    def test_creates_directory_and_file(self, tmp_path, monkeypatch):
        """Test that ensure_state_file creates the directory and file."""
        # Mock the global paths to point to tmp_path
        import code.serialize_and_hash as mod
        original_dir = mod.STATE_DIR
        original_file = mod.STATE_FILE
        
        mod.STATE_DIR = tmp_path / "state" / "projects"
        mod.STATE_FILE = mod.STATE_DIR / "test.yaml"
        
        mod.ensure_state_file()
        
        assert mod.STATE_DIR.exists()
        assert mod.STATE_FILE.exists()
        
        # Restore
        mod.STATE_DIR = original_dir
        mod.STATE_FILE = original_file

    def test_initializes_schema(self, tmp_path, monkeypatch):
        """Test that the created file has the correct initial schema."""
        import code.serialize_and_hash as mod
        mod.STATE_DIR = tmp_path / "state" / "projects"
        mod.STATE_FILE = mod.STATE_DIR / "test.yaml"
        
        mod.ensure_state_file()
        
        with open(mod.STATE_FILE, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "artifact_hashes" in data
        assert isinstance(data["artifact_hashes"], dict)

class TestUpdateStateFile:
    def test_updates_existing_file(self, tmp_path, monkeypatch):
        """Test updating an existing state file."""
        import code.serialize_and_hash as mod
        mod.STATE_DIR = tmp_path / "state" / "projects"
        mod.STATE_FILE = mod.STATE_DIR / "test.yaml"
        
        # Create initial file
        mod.ensure_state_file()
        
        # Update
        mod.update_state_file("file1.json", "hash1")
        
        with open(mod.STATE_FILE, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["artifact_hashes"]["file1.json"] == "hash1"

    def test_merges_new_hashes(self, tmp_path, monkeypatch):
        """Test that new hashes are merged without overwriting others."""
        import code.serialize_and_hash as mod
        mod.STATE_DIR = tmp_path / "state" / "projects"
        mod.STATE_FILE = mod.STATE_DIR / "test.yaml"
        
        mod.ensure_state_file()
        mod.update_state_file("file1.json", "hash1")
        mod.update_state_file("file2.json", "hash2")
        
        with open(mod.STATE_FILE, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["artifact_hashes"]["file1.json"] == "hash1"
        assert data["artifact_hashes"]["file2.json"] == "hash2"