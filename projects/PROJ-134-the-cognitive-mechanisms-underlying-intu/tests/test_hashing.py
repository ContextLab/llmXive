"""
Unit tests for the hashing utilities (T018).

Tests the SHA-256 calculation, state file updates, and verification logic.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from code.utils.hashing import (
    calculate_sha256,
    update_state_yaml,
    verify_artifact,
    checksum_derived_datasets
)
from code.config import PROJECT_ROOT


class TestHashingUtils:
    """Tests for the hashing utility functions."""

    def test_calculate_sha256_simple(self, tmp_path):
        """Test SHA-256 calculation on a simple file."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        # Calculate checksum
        checksum = calculate_sha256(test_file)
        
        # Verify it's a valid hex string of correct length
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")

    def test_calculate_sha256_directory(self, tmp_path):
        """Test that ValueError is raised for directories."""
        with pytest.raises(ValueError):
            calculate_sha256(tmp_path)

    def test_update_state_yaml_creates_file(self, tmp_path):
        """Test that update_state_yaml creates the state file if missing."""
        state_file = tmp_path / "state" / "checksums.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        update_state_yaml(
            artifact_path="data/processed/test.csv",
            checksum="abc123",
            state_file=state_file
        )
        
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert "artifacts" in data
        assert "data/processed/test.csv" in data["artifacts"]
        assert data["artifacts"]["data/processed/test.csv"]["checksum"] == "abc123"

    def test_update_state_yaml_updates_existing(self, tmp_path):
        """Test that update_state_yaml updates existing entries."""
        state_file = tmp_path / "state" / "checksums.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create initial state
        initial_data = {
            "artifacts": {
                "data/processed/existing.csv": {"checksum": "old_hash"}
            }
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_data, f)
        
        # Update with new artifact
        update_state_yaml(
            artifact_path="data/processed/new.csv",
            checksum="new_hash",
            state_file=state_file
        )
        
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert "data/processed/existing.csv" in data["artifacts"]
        assert "data/processed/new.csv" in data["artifacts"]
        assert data["artifacts"]["data/processed/new.csv"]["checksum"] == "new_hash"

    def test_verify_artifact_success(self, tmp_path):
        """Test successful artifact verification."""
        test_file = tmp_path / "verify_test.txt"
        content = "Verification content"
        test_file.write_text(content)
        
        checksum = calculate_sha256(test_file)
        
        assert verify_artifact(test_file, checksum) is True

    def test_verify_artifact_failure(self, tmp_path):
        """Test failed artifact verification with wrong checksum."""
        test_file = tmp_path / "verify_test.txt"
        test_file.write_text("Content")
        
        assert verify_artifact(test_file, "wrong_checksum") is False

    def test_checksum_derived_datasets_empty(self, tmp_path, monkeypatch):
        """Test checksumming when no datasets exist."""
        # Mock PROJECT_ROOT to use tmp_path
        monkeypatch.setattr("code.utils.hashing.PROJECT_ROOT", tmp_path)
        
        # Ensure processed dir exists but is empty
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        
        results = checksum_derived_datasets()
        assert results == {}

    def test_checksum_derived_datasets_with_files(self, tmp_path, monkeypatch):
        """Test checksumming when datasets exist."""
        monkeypatch.setattr("code.utils.hashing.PROJECT_ROOT", tmp_path)
        
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test CSV
        test_csv = processed_dir / "test.csv"
        test_csv.write_text("col1,col2\n1,2\n")
        
        results = checksum_derived_datasets()
        
        assert "data/processed/test.csv" in results
        assert len(results["data/processed/test.csv"]) == 64

    def test_state_file_updated_after_checksum(self, tmp_path, monkeypatch):
        """Test that state file is updated when checksumming datasets."""
        monkeypatch.setattr("code.utils.hashing.PROJECT_ROOT", tmp_path)
        
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        test_csv = processed_dir / "test.csv"
        test_csv.write_text("data")
        
        checksum_derived_datasets()
        
        state_file = tmp_path / "state" / "checksums.yaml"
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert "data/processed/test.csv" in data["artifacts"]
        assert data["artifacts"]["data/processed/test.csv"]["status"] == "verified"