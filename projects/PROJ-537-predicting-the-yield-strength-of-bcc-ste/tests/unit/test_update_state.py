import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.update_state import load_checksums, load_or_create_state, update_state_with_checksums, save_state

class TestLoadChecksums:
    def test_load_checksums_from_file(self, tmp_path):
        # Create a test checksum file
        checksum_file = tmp_path / "checksums.txt"
        content = """data/raw/experimental.csv: abc123
        data/intermediate/merged.csv: def456
        data/results/output.json: ghi789"""
        checksum_file.write_text(content)
        
        result = load_checksums(checksum_file)
        
        assert "data/raw/experimental.csv" in result
        assert result["data/raw/experimental.csv"] == "abc123"
        assert "data/intermediate/merged.csv" in result
        assert result["data/intermediate/merged.csv"] == "def456"
        assert "data/results/output.json" in result
        assert result["data/results/output.json"] == "ghi789"

    def test_load_checksums_missing_file(self, tmp_path):
        result = load_checksums(tmp_path / "nonexistent.txt")
        assert result == {}

    def test_load_checksums_with_space_separator(self, tmp_path):
        checksum_file = tmp_path / "checksums.txt"
        content = "data/raw/file.csv abc123\ndata/intermediate/file.csv def456"
        checksum_file.write_text(content)
        
        result = load_checksums(checksum_file)
        
        assert "data/raw/file.csv" in result
        assert result["data/raw/file.csv"] == "abc123"

class TestLoadOrCreateState:
    def test_load_existing_state(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "artifacts": {"old.txt": "hash123"}
        }
        state_file.write_text(yaml.dump(initial_state))
        
        result = load_or_create_state(state_file)
        
        assert result["project_id"] == "TEST-001"
        assert "old.txt" in result["artifacts"]

    def test_create_new_state(self, tmp_path):
        state_file = tmp_path / "new_state.yaml"
        
        result = load_or_create_state(state_file)
        
        assert "project_id" in result
        assert "artifacts" in result
        assert isinstance(result["artifacts"], dict)
        assert result["artifacts"] == {}

class TestUpdateStateWithChecksums:
    def test_update_state_with_single_checksum(self):
        state = {
            "project_id": "TEST-001",
            "artifacts": {}
        }
        checksums = {"data/file.csv": "abc123"}
        
        update_state_with_checksums(state, checksums)
        
        assert "data/file.csv" in state["artifacts"]
        assert state["artifacts"]["data/file.csv"]["hash"] == "abc123"
        assert state["artifacts"]["data/file.csv"]["type"] == "sha256"
        assert "last_updated" in state

    def test_update_state_with_multiple_checksums(self):
        state = {
            "project_id": "TEST-001",
            "artifacts": {}
        }
        checksums = {
            "data/file1.csv": "hash1",
            "data/file2.csv": "hash2",
            "data/results/output.json": "hash3"
        }
        
        update_state_with_checksums(state, checksums)
        
        assert len(state["artifacts"]) == 3
        assert state["artifacts"]["data/file1.csv"]["hash"] == "hash1"
        assert state["artifacts"]["data/file2.csv"]["hash"] == "hash2"
        assert state["artifacts"]["data/results/output.json"]["hash"] == "hash3"

class TestSaveState:
    def test_save_state_creates_file(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state = {"project_id": "TEST-001", "artifacts": {}}
        
        save_state(state, state_file)
        
        assert state_file.exists()
        
        # Verify content
        with open(state_file, 'r') as f:
            loaded_state = yaml.safe_load(f)
        
        assert loaded_state["project_id"] == "TEST-001"

    def test_save_state_creates_directories(self, tmp_path):
        state_file = tmp_path / "subdir" / "deep" / "state.yaml"
        state = {"project_id": "TEST-001"}
        
        save_state(state, state_file)
        
        assert state_file.exists()
        assert state_file.parent.exists()