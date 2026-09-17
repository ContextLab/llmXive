import json
import os
import tempfile
from pathlib import Path
import pytest
import hashlib

# Import the module under test
import sys
sys.path.insert(0, 'code')
from serialize_and_hash import compute_sha256, validate_ast_params, ensure_state_file, update_state_file

class TestComputeSha256:
    def test_compute_sha256_simple(self, tmp_path):
        """Test SHA-256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(nonexistent)

class TestValidateAstParams:
    def test_valid_ast_params(self):
        """Test validation with valid ast_params."""
        data = {
            "repo_slug": "test/repo",
            "ast_params": ["param1", "param2"],
            "methods": []
        }
        assert validate_ast_params(data) is True
    
    def test_missing_ast_params(self):
        """Test validation when ast_params is missing."""
        data = {
            "repo_slug": "test/repo",
            "methods": []
        }
        assert validate_ast_params(data) is False
    
    def test_ast_params_not_list(self):
        """Test validation when ast_params is not a list."""
        data = {
            "repo_slug": "test/repo",
            "ast_params": "not_a_list",
            "methods": []
        }
        assert validate_ast_params(data) is False
    
    def test_data_not_dict(self):
        """Test validation when data is not a dictionary."""
        assert validate_ast_params([]) is False
        assert validate_ast_params("string") is False
        assert validate_ast_params(None) is False

class TestEnsureStateFile:
    def test_creates_new_file(self, tmp_path):
        """Test that ensure_state_file creates a new file if missing."""
        state_file = tmp_path / "state.yaml"
        
        result = ensure_state_file(state_file)
        
        assert state_file.exists()
        assert result == {"artifact_hashes": {}}
        
        # Verify file content
        content = state_file.read_text()
        assert "artifact_hashes: {}" in content
    
    def test_loads_existing_file(self, tmp_path):
        """Test that ensure_state_file loads existing file."""
        state_file = tmp_path / "state.yaml"
        initial_content = "artifact_hashes: {\n  'file1.json': 'hash1'\n}\n"
        state_file.write_text(initial_content)
        
        result = ensure_state_file(state_file)
        
        assert result == {"artifact_hashes": {"file1.json": "hash1"}}
    
    def test_handles_empty_file(self, tmp_path):
        """Test handling of empty file."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("")
        
        result = ensure_state_file(state_file)
        
        assert result == {"artifact_hashes": {}}

class TestUpdateStateFile:
    def test_adds_new_hash(self, tmp_path):
        """Test adding a new hash to state file."""
        state_file = tmp_path / "state.yaml"
        
        # Initialize file
        ensure_state_file(state_file)
        
        # Update with new hash
        update_state_file(state_file, "test.json", "abc123")
        
        # Verify
        result = ensure_state_file(state_file)
        assert "test.json" in result["artifact_hashes"]
        assert result["artifact_hashes"]["test.json"] == "abc123"
    
    def test_overwrites_existing_hash(self, tmp_path):
        """Test overwriting an existing hash."""
        state_file = tmp_path / "state.yaml"
        
        # Initialize with existing hash
        ensure_state_file(state_file)
        update_state_file(state_file, "test.json", "old_hash")
        
        # Update with new hash
        update_state_file(state_file, "test.json", "new_hash")
        
        # Verify
        result = ensure_state_file(state_file)
        assert result["artifact_hashes"]["test.json"] == "new_hash"
    
    def test_multiple_hashes(self, tmp_path):
        """Test adding multiple hashes."""
        state_file = tmp_path / "state.yaml"
        ensure_state_file(state_file)
        
        update_state_file(state_file, "file1.json", "hash1")
        update_state_file(state_file, "file2.json", "hash2")
        
        result = ensure_state_file(state_file)
        assert len(result["artifact_hashes"]) == 2
        assert result["artifact_hashes"]["file1.json"] == "hash1"
        assert result["artifact_hashes"]["file2.json"] == "hash2"
