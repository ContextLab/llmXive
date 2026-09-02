"""
Contract test for T050: Verify all artifacts are checksummed in state/

This test ensures that the checksum verification script:
1. Correctly computes SHA-256 hashes
2. Properly loads and saves the hash registry
3. Detects checksum mismatches
4. Handles missing artifacts gracefully
"""
import os
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import setup_logging
from code_08_verify_artifacts_checksums import (
    compute_sha256,
    load_hash_registry,
    save_hash_registry,
    verify_artifact,
    get_project_root
)


class TestComputeSHA256:
    """Tests for compute_sha256 function."""

    def test_compute_sha256_correct_hash(self, tmp_path):
        """Verify SHA-256 computation for a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash

    def test_compute_sha256_empty_file(self, tmp_path):
        """Verify SHA-256 for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash

    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Verify error handling for nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(IOError):
            compute_sha256(test_file)


class TestLoadSaveHashRegistry:
    """Tests for load_hash_registry and save_hash_registry."""

    def test_save_and_load_registry(self, tmp_path):
        """Verify registry can be saved and loaded correctly."""
        registry_path = tmp_path / "registry.json"
        
        # Mock the get_project_root to use tmp_path
        test_registry = {
            "data/raw/test.parquet": "abc123",
            "output/report.csv": "def456"
        }
        
        with patch('code_08_verify_artifacts_checksums.HASH_REGISTRY_PATH', str(registry_path.relative_to(tmp_path))):
            with patch('code_08_verify_artifacts_checksums.get_project_root', return_value=tmp_path):
                # Save
                save_hash_registry(test_registry)
                
                # Load
                loaded = load_hash_registry()
                
                assert loaded == test_registry

    def test_load_empty_registry(self, tmp_path):
        """Verify handling of empty/missing registry."""
        with patch('code_08_verify_artifacts_checksums.get_project_root', return_value=tmp_path):
            registry = load_hash_registry()
            assert registry == {}

    def test_load_invalid_json(self, tmp_path):
        """Verify error handling for invalid JSON."""
        registry_path = tmp_path / "state" / "data_hashes.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text("invalid json {")
        
        with patch('code_08_verify_artifacts_checksums.get_project_root', return_value=tmp_path):
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_hash_registry()


class TestVerifyArtifact:
    """Tests for verify_artifact function."""

    def test_verify_success(self, tmp_path):
        """Verify successful checksum verification."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        success, message = verify_artifact(test_file, expected_hash)
        
        assert success is True
        assert message == "OK"

    def test_verify_failure(self, tmp_path):
        """Verify failed checksum verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        success, message = verify_artifact(test_file, "wrong_hash")
        
        assert success is False
        assert "Mismatch" in message


class TestGetProjectRoot:
    """Tests for get_project_root function."""

    def test_get_project_root_finds_root(self):
        """Verify project root detection."""
        root = get_project_root()
        assert (root / "code").exists()
        assert (root / "data").exists()