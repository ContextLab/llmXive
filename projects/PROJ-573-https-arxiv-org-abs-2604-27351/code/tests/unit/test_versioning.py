"""
Unit tests for versioning utilities (T018).
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
from datetime import datetime, timezone
import time

# Import the module under test
# Adjust import path based on project structure (src.utils.versioning)
from src.utils.versioning import update_artifact_timestamp, update_timestamp_on_change


class TestVersioningUtils:
    """Test cases for versioning utility functions."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create a temporary directory structure for state files."""
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir

    @pytest.fixture
    def sample_state_file(self, temp_state_dir):
        """Create a sample state file."""
        state_file = temp_state_dir / "PROJ-573-https-arxiv-org-abs-2604-27351.yaml"
        data = {
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": "2023-01-01T00:00:00+00:00",
            "artifact_hashes": {}
        }
        with open(state_file, 'w') as f:
            yaml.dump(data, f)
        return state_file

    def test_update_artifact_timestamp_updates_time(self, sample_state_file):
        """Test that update_artifact_timestamp updates the updated_at field."""
        # Record initial time
        initial_time = datetime.now(timezone.utc)
        time.sleep(0.1)  # Small delay to ensure time difference
        
        # Call the function
        result = update_artifact_timestamp(
            "test_artifact.txt", 
            "PROJ-573-https-arxiv-org-abs-2604-27351"
        )
        
        # Verify success
        assert result is True
        
        # Verify file was updated
        with open(sample_state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check updated_at is newer than created_at
        assert data["updated_at"] >= data["created_at"]
        # Parse and verify it's a valid ISO format timestamp
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        assert updated_at >= initial_time

    def test_update_artifact_timestamp_creates_new_file(self, temp_state_dir):
        """Test that update_artifact_timestamp creates a new state file if it doesn't exist."""
        new_project_id = "PROJ-NEW-TEST"
        state_file = temp_state_dir / f"{new_project_id}.yaml"
        
        # Ensure file doesn't exist
        assert not state_file.exists()
        
        # Call the function
        result = update_artifact_timestamp("new_artifact.txt", new_project_id)
        
        # Verify success and file creation
        assert result is True
        assert state_file.exists()
        
        # Verify structure
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["project_id"] == new_project_id
        assert "created_at" in data
        assert "updated_at" in data
        assert "artifact_hashes" in data

    def test_update_timestamp_on_change_wrapper(self, sample_state_file):
        """Test that update_timestamp_on_change wrapper function works correctly."""
        initial_time = datetime.now(timezone.utc)
        time.sleep(0.1)
        
        result = update_timestamp_on_change(
            "wrapped_artifact.txt", 
            "PROJ-573-https-arxiv-org-abs-2604-27351"
        )
        
        assert result is True
        
        with open(sample_state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        assert updated_at >= initial_time

    def test_invalid_project_id_handling(self, temp_state_dir):
        """Test behavior with invalid project ID (should create new file)."""
        result = update_artifact_timestamp(
            "test.txt", 
            "INVALID-PROJECT-ID"
        )
        
        # Should succeed by creating a new file
        assert result is True
        
        state_file = temp_state_dir / "INVALID-PROJECT-ID.yaml"
        assert state_file.exists()