"""
Tests for versioning module.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml
from src.versioning import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact
)

class TestComputeSha256:
    def test_compute_sha256(self):
        """Test SHA256 computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)
        hash1 = compute_sha256(path)
        hash2 = compute_sha256(path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        os.unlink(path)

class TestLoadSaveState:
    def test_load_save_state(self):
        """Test state loading and saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.yaml"
            state = {"artifacts": {"test": {"hash": "abc"}}}
            # Temporarily override STATE_FILE
            import src.versioning
            original_state_file = src.versioning.STATE_FILE
            src.versioning.STATE_FILE = state_file
            try:
                save_state(state)
                loaded = load_state()
                assert loaded == state
            finally:
                src.versioning.STATE_FILE = original_state_file

class TestUpdateArtifactState:
    def test_update_artifact_state(self):
        """Test artifact state update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            state_file = Path(tmpdir) / "state.yaml"
            import src.versioning
            original_state_file = src.versioning.STATE_FILE
            src.versioning.STATE_FILE = state_file
            try:
                update_artifact_state("test", test_file)
                state = load_state()
                assert "test" in state["artifacts"]
                assert state["artifacts"]["test"]["hash"] == compute_sha256(test_file)
            finally:
                src.versioning.STATE_FILE = original_state_file

class TestVerifyArtifact:
    def test_verify_artifact(self):
        """Test artifact verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            state_file = Path(tmpdir) / "state.yaml"
            import src.versioning
            original_state_file = src.versioning.STATE_FILE
            src.versioning.STATE_FILE = state_file
            try:
                update_artifact_state("test", test_file)
                assert verify_artifact("test", test_file)
                # Modify file
                test_file.write_text("changed")
                assert not verify_artifact("test", test_file)
            finally:
                src.versioning.STATE_FILE = original_state_file
