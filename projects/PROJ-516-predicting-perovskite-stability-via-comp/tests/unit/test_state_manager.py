"""
Unit tests for the state_manager module.
"""
import os
import tempfile
from pathlib import Path
import yaml
import pytest

from utils.state_manager import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact,
    update_state_for_multiple_artifacts
)


def test_compute_sha256():
    """Test that SHA-256 is computed correctly for a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"test content"
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # "test content" SHA-256
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        result = compute_sha256(tmp_path)
        assert result == expected
    finally:
        tmp_path.unlink()


def test_load_state_missing():
    """Test loading state from a non-existent file returns empty structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "nonexistent.yaml"
        state = load_state(state_path)
        assert state["artifacts"] == {}
        assert state["last_updated"] is None


def test_save_and_load_state():
    """Test saving and loading state preserves data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        initial_state = {
            "artifacts": {"data/test.csv": {"hash": "abc123", "size_bytes": 100}},
            "last_updated": "2023-01-01T00:00:00Z"
        }
        save_state(state_path, initial_state)
        
        loaded_state = load_state(state_path)
        assert loaded_state["artifacts"]["data/test.csv"]["hash"] == "abc123"
        assert loaded_state["last_updated"] == "2023-01-01T00:00:00Z"


def test_update_artifact_state():
    """Test updating state with a new artifact."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy file
        file_path = Path(tmpdir) / "artifact.txt"
        file_path.write_text("hello")
        
        state = {"artifacts": {}}
        artifact_rel_path = "data/artifact.txt"
        
        state = update_artifact_state(state, artifact_rel_path, file_path)
        
        assert artifact_rel_path in state["artifacts"]
        assert "hash" in state["artifacts"][artifact_rel_path]
        assert "size_bytes" in state["artifacts"][artifact_rel_path]
        assert "updated_at" in state["artifacts"][artifact_rel_path]


def test_verify_artifact_valid():
    """Test verification passes when hash matches."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "verify.txt"
        content = b"verify me"
        file_path.write_bytes(content)
        
        file_hash = compute_sha256(file_path)
        state = {
            "artifacts": {
                "data/verify.txt": {"hash": file_hash}
            }
        }
        
        assert verify_artifact(state, "data/verify.txt", file_path) is True


def test_verify_artifact_invalid():
    """Test verification fails when hash does not match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "verify.txt"
        file_path.write_text("change me")
        
        # Use a fake hash
        state = {
            "artifacts": {
                "data/verify.txt": {"hash": "invalid_hash_12345"}
            }
        }
        
        assert verify_artifact(state, "data/verify.txt", file_path) is False


def test_update_state_for_multiple_artifacts():
    """Test updating state for multiple files at once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        
        # Create two files
        file1 = Path(tmpdir) / "f1.txt"
        file1.write_text("file1")
        file2 = Path(tmpdir) / "f2.txt"
        file2.write_text("file2")
        
        artifacts = [
            {"relative_path": "data/f1.txt", "absolute_path": str(file1)},
            {"relative_path": "data/f2.txt", "absolute_path": str(file2)}
        ]
        
        update_state_for_multiple_artifacts(state_path, artifacts)
        
        state = load_state(state_path)
        assert "data/f1.txt" in state["artifacts"]
        assert "data/f2.txt" in state["artifacts"]
        assert state["last_updated"] is not None
