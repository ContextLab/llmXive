import os
import yaml
import pytest
from pathlib import Path

# Import the function we just created
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_state import create_state_structure

class TestStateInitialization:
    """
    Tests for task T001d: State directory and placeholder file creation.
    """

    def test_state_directory_created(self, tmp_path):
        """Verify that state/projects/ directory is created."""
        create_state_structure(str(tmp_path))
        
        state_dir = tmp_path / "state" / "projects"
        assert state_dir.exists(), "state/projects/ directory should exist"
        assert state_dir.is_dir(), "state/projects/ should be a directory"

    def test_project_yaml_created(self, tmp_path):
        """Verify that the specific project YAML file is created."""
        create_state_structure(str(tmp_path))
        
        project_id = "PROJ-122-identifying-structure-property-relations"
        state_file = tmp_path / "state" / "projects" / f"{project_id}.yaml"
        
        assert state_file.exists(), f"{state_file} should exist"
        assert state_file.is_file(), f"{state_file} should be a file"

    def test_yaml_content_structure(self, tmp_path):
        """Verify the YAML file contains expected keys and structure."""
        create_state_structure(str(tmp_path))
        
        project_id = "PROJ-122-identifying-structure-property-relations"
        state_file = tmp_path / "state" / "projects" / f"{project_id}.yaml"
        
        with open(state_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        
        # Check top-level keys
        assert "project_id" in content
        assert "status" in content
        assert "artifacts" in content
        assert "execution_history" in content
        
        # Check specific values
        assert content["project_id"] == project_id
        assert content["status"] == "initialized"
        
        # Check artifacts structure
        artifacts = content["artifacts"]
        assert "data/raw" in artifacts
        assert "data/processed" in artifacts
        assert "data/features" in artifacts
        assert "figures" in artifacts

    def test_no_overwrite_existing(self, tmp_path):
        """Verify that running twice doesn't crash (idempotency)."""
        # Run once
        create_state_structure(str(tmp_path))
        
        # Run again
        create_state_structure(str(tmp_path))
        
        # Should still exist
        project_id = "PROJ-122-identifying-structure-property-relations"
        state_file = tmp_path / "state" / "projects" / f"{project_id}.yaml"
        assert state_file.exists()