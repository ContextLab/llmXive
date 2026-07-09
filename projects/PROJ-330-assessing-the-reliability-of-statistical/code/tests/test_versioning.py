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
from src.config import PROJECT_ROOT, STATE_FILE

class TestComputeSha256:
    def test_compute_sha256_valid_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        hash_val = compute_sha256(test_file)
        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_compute_sha256_empty_file(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        hash_val = compute_sha256(test_file)
        assert len(hash_val) == 64

    def test_compute_sha256_file_not_found(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)

class TestLoadSaveState:
    def test_load_state_empty_file(self, tmp_path, monkeypatch):
        # Monkeypatch PROJECT_ROOT and STATE_FILE to use tmp_path
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr("src.config.STATE_FILE", tmp_path / "state.yaml")
        
        state = load_state()
        assert state == {"artifacts": {}}

    def test_save_state_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        test_state = {"artifacts": {"test": {"sha256": "abc123"}}}
        save_state(test_state)
        
        loaded = load_state()
        assert loaded == test_state

    def test_load_invalid_yaml_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        state_file.write_text("invalid: yaml: content: [")
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        state = load_state()
        assert state == {"artifacts": {}}

class TestUpdateArtifactState:
    def test_update_existing_artifact(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        artifact_file = tmp_path / "data" / "test.csv"
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("col1,col2\n1,2")
        
        update_artifact_state("test_artifact", artifact_file)
        
        state = load_state()
        assert "test_artifact" in state["artifacts"]
        assert state["artifacts"]["test_artifact"]["sha256"] is not None
        assert state["artifacts"]["test_artifact"]["path"] == "data/test.csv"

    def test_update_nonexistent_artifact(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        non_existent = tmp_path / "missing.csv"
        
        update_artifact_state("missing_artifact", non_existent)
        
        state = load_state()
        assert "missing_artifact" in state["artifacts"]
        assert state["artifacts"]["missing_artifact"]["sha256"] is None
        assert "error" in state["artifacts"]["missing_artifact"]

class TestVerifyArtifact:
    def test_verify_correct_hash(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        # Create a test file and update state
        artifact_file = tmp_path / "verify_test.txt"
        artifact_file.write_text("verify content")
        update_artifact_state("verify_art", artifact_file)
        
        state = load_state()
        expected_hash = state["artifacts"]["verify_art"]["sha256"]
        
        assert verify_artifact("verify_art", expected_hash) is True

    def test_verify_wrong_hash(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        artifact_file = tmp_path / "wrong_test.txt"
        artifact_file.write_text("wrong content")
        update_artifact_state("wrong_art", artifact_file)
        
        assert verify_artifact("wrong_art", "invalid_hash_123") is False

    def test_verify_missing_artifact(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.PROJECT_ROOT", tmp_path)
        state_file = tmp_path / "state.yaml"
        monkeypatch.setattr("src.config.STATE_FILE", state_file)
        
        assert verify_artifact("nonexistent_art", "any_hash") is False