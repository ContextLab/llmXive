"""
Unit tests for the state initialization script (T007).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import yaml
import pytest

# Add parent directory to path to import scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.init_state import init_state_file

class TestInitState:
    def test_creates_directory_and_file(self, tmp_path):
        """Test that init_state_file creates the project directory and state.yaml."""
        project_id = "PROJ-TEST"
        state_root = tmp_path / "state"
        
        result = init_state_file(project_id, state_root)
        
        assert result is True
        assert (state_root / project_id).exists()
        assert (state_root / project_id / "state.yaml").exists()

    def test_schema_correctness(self, tmp_path):
        """Test that the generated state.yaml has the correct schema."""
        project_id = "PROJ-SCHEMA"
        state_root = tmp_path / "state"
        
        init_state_file(project_id, state_root)
        
        state_file = state_root / project_id / "state.yaml"
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "project_id" in data
        assert "created_at" in data
        assert "artifact_hashes" in data
        assert isinstance(data["artifact_hashes"], dict)
        assert data["project_id"] == project_id

    def test_artifact_hashes_empty_initially(self, tmp_path):
        """Test that artifact_hashes is an empty dictionary on initialization."""
        project_id = "PROJ-EMPTY"
        state_root = tmp_path / "state"
        
        init_state_file(project_id, state_root)
        
        state_file = state_root / project_id / "state.yaml"
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["artifact_hashes"] == {}

    def test_created_at_format(self, tmp_path):
        """Test that created_at is a valid ISO format string."""
        project_id = "PROJ-DATE"
        state_root = tmp_path / "state"
        
        init_state_file(project_id, state_root)
        
        state_file = state_root / project_id / "state.yaml"
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        created_at = data["created_at"]
        assert isinstance(created_at, str)
        # Basic check for ISO format presence (Z or +00:00)
        assert "T" in created_at
        assert ("Z" in created_at or "+" in created_at or "-" in created_at)