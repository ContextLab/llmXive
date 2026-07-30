"""
Unit tests for T020b: Update Single Source of Truth.

Tests the functionality of updating the project state YAML file with artifact checksums.
"""
import os
import json
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code_020b_update_state import (
    load_existing_state,
    update_artifacts_with_checksums,
    write_state_file,
    PROJECT_ID
)

class TestLoadExistingState:
    """Tests for load_existing_state function."""
    
    def test_load_nonexistent_state_creates_default(self, tmp_path):
        """Test that loading a non-existent state creates a default structure."""
        non_existent_file = tmp_path / "non_existent.yaml"
        
        # Mock the STATE_FILE path
        with patch('code_020b_update_state.STATE_FILE', non_existent_file):
            state = load_existing_state()
        
        assert state["project_id"] == PROJECT_ID
        assert "created_at" in state
        assert state["artifacts"] == {}
        assert state["status"] == "in_progress"
    
    def test_load_existing_state_preserves_data(self, tmp_path):
        """Test that loading an existing state preserves its data."""
        existing_file = tmp_path / "existing.yaml"
        original_state = {
            "project_id": PROJECT_ID,
            "created_at": "2024-01-01T00:00:00",
            "artifacts": {"old_file.csv": {"checksum": "abc123"}},
            "status": "in_progress"
        }
        
        with open(existing_file, 'w') as f:
            yaml.dump(original_state, f)
        
        with patch('code_020b_update_state.STATE_FILE', existing_file):
            state = load_existing_state()
        
        assert state["project_id"] == PROJECT_ID
        assert state["created_at"] == "2024-01-01T00:00:00"
        assert "old_file.csv" in state["artifacts"]
        assert state["artifacts"]["old_file.csv"]["checksum"] == "abc123"

class TestUpdateArtifactsWithChecksums:
    """Tests for update_artifacts_with_checksums function."""
    
    def test_add_new_checksums(self):
        """Test adding new checksums to an empty state."""
        state = {"artifacts": {}}
        checksums = {
            "data/raw/polymer_data.csv": "sha256_hash_123",
            "data/processed/features.csv": "sha256_hash_456"
        }
        
        updated_state = update_artifacts_with_checksums(state, checksums)
        
        assert len(updated_state["artifacts"]) == 2
        assert "data/raw/polymer_data.csv" in updated_state["artifacts"]
        assert "data/processed/features.csv" in updated_state["artifacts"]
        assert updated_state["artifacts"]["data/raw/polymer_data.csv"]["checksum"] == "sha256_hash_123"
        assert "last_verified" in updated_state["artifacts"]["data/raw/polymer_data.csv"]
    
    def test_update_existing_checksums(self):
        """Test updating existing checksums with new values."""
        state = {
            "artifacts": {
                "data/raw/polymer_data.csv": {
                    "checksum": "old_hash",
                    "last_verified": "2024-01-01T00:00:00"
                }
            }
        }
        checksums = {
            "data/raw/polymer_data.csv": "sha256_hash_new"
        }
        
        updated_state = update_artifacts_with_checksums(state, checksums)
        
        assert updated_state["artifacts"]["data/raw/polymer_data.csv"]["checksum"] == "sha256_hash_new"
        assert "last_verified" in updated_state["artifacts"]["data/raw/polymer_data.csv"]
    
    def test_handle_checksum_dict_format(self):
        """Test handling checksums provided as dictionaries with metadata."""
        state = {"artifacts": {}}
        checksums = {
            "data/raw/test.csv": {
                "checksum": "sha256_hash_789",
                "size": 1024,
                "timestamp": "2024-01-01"
            }
        }
        
        updated_state = update_artifacts_with_checksums(state, checksums)
        
        assert updated_state["artifacts"]["data/raw/test.csv"]["checksum"] == "sha256_hash_789"
    
    def test_empty_checksums_dict(self):
        """Test handling an empty checksums dictionary."""
        state = {"artifacts": {"existing": {"checksum": "abc"}}}
        checksums = {}
        
        updated_state = update_artifacts_with_checksums(state, checksums)
        
        # Should preserve existing artifacts
        assert len(updated_state["artifacts"]) == 1

class TestWriteStateFile:
    """Tests for write_state_file function."""
    
    def test_write_creates_file_and_directory(self, tmp_path):
        """Test that writing creates the file and necessary directories."""
        output_path = tmp_path / "subdir" / "state.yaml"
        state = {
            "project_id": PROJECT_ID,
            "artifacts": {},
            "status": "in_progress"
        }
        
        write_state_file(state, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            written_state = yaml.safe_load(f)
        
        assert written_state["project_id"] == PROJECT_ID
        assert "updated_at" in written_state
        assert "last_task_completed" in written_state
    
    def test_write_updates_timestamps(self, tmp_path):
        """Test that writing updates timestamps."""
        output_path = tmp_path / "state.yaml"
        state = {
            "project_id": PROJECT_ID,
            "artifacts": {},
            "updated_at": "2024-01-01T00:00:00",
            "last_task_completed": "T019"
        }
        
        write_state_file(state, output_path)
        
        with open(output_path, 'r') as f:
            written_state = yaml.safe_load(f)
        
        # updated_at should be different (newer)
        assert written_state["updated_at"] != "2024-01-01T00:00:00"
        assert written_state["last_task_completed"] == "T020b"

class TestIntegration:
    """Integration tests for the complete T020b workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test the complete workflow from loading state to writing updated state."""
        # Setup
        state_file = tmp_path / "state.yaml"
        checksums_file = tmp_path / "checksums.json"
        
        # Create initial state
        initial_state = {
            "project_id": PROJECT_ID,
            "created_at": "2024-01-01T00:00:00",
            "artifacts": {},
            "status": "in_progress"
        }
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Create checksums manifest
        checksums_data = {
            "data/raw/polymer_data.csv": "sha256_hash_abc",
            "data/processed/features.csv": {
                "checksum": "sha256_hash_def",
                "size": 2048
            }
        }
        with open(checksums_file, 'w') as f:
            json.dump(checksums_data, f)
        
        # Mock paths
        with patch('code_020b_update_state.STATE_FILE', state_file):
            with patch('code_020b_update_state.CHECKSUMS_MANIFEST', checksums_file):
                # Reload module to pick up new paths (or use the functions directly)
                from code_020b_update_state import main as t020b_main
                
                # Run the main function logic (without actual logging setup)
                state = load_existing_state()
                checksums = checksums_data  # Simulate load_checksums
                state = update_artifacts_with_checksums(state, checksums)
                write_state_file(state, state_file)
        
        # Verify
        with open(state_file, 'r') as f:
            final_state = yaml.safe_load(f)
        
        assert final_state["artifacts"]["data/raw/polymer_data.csv"]["checksum"] == "sha256_hash_abc"
        assert final_state["artifacts"]["data/processed/features.csv"]["checksum"] == "sha256_hash_def"
        assert final_state["last_task_completed"] == "T020b"
        assert "updated_at" in final_state