"""
Unit tests for the finalize_state_registry module.
"""
import os
import sys
import yaml
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.finalize_state_registry import (
    compute_sha256,
    collect_all_artifact_hashes,
    update_state_registry,
    PROJECT_ID,
    DATA_DIRS
)

class TestComputeSha256:
    def test_compute_hash_for_file(self, tmp_path):
        """Test SHA-256 computation for a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_compute_hash_for_nonexistent_file(self):
        """Test that None is returned for nonexistent files."""
        assert compute_sha256(Path("/nonexistent/file.txt")) is None

class TestCollectAllArtifactHashes:
    def test_collect_hashes_from_empty_directory(self, tmp_path):
        """Test hash collection from an empty directory."""
        # Create a temporary data directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "processed").mkdir()
        (data_dir / "results").mkdir()
        
        # Temporarily change working directory
        old_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            hashes = collect_all_artifact_hashes([
                Path("data/raw"),
                Path("data/processed"),
                Path("data/results")
            ])
            assert hashes == {}
        finally:
            os.chdir(old_cwd)
    
    def test_collect_hashes_from_populated_directory(self, tmp_path):
        """Test hash collection from a directory with files."""
        # Create a temporary data directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        raw_dir = data_dir / "raw"
        raw_dir.mkdir()
        
        # Create test files
        test_file = raw_dir / "test_workflow.json"
        test_content = b'{"id": "test"}'
        test_file.write_bytes(test_content)
        
        # Temporarily change working directory
        old_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            hashes = collect_all_artifact_hashes([Path("data/raw")])
            assert len(hashes) == 1
            assert "raw/test_workflow.json" in hashes
            assert hashes["raw/test_workflow.json"] == hashlib.sha256(test_content).hexdigest()
        finally:
            os.chdir(old_cwd)
    
    def test_excludes_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are excluded from hashing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        raw_dir = data_dir / "raw"
        raw_dir.mkdir()
        
        # Create a .gitkeep file
        gitkeep = raw_dir / ".gitkeep"
        gitkeep.write_bytes(b"")
        
        # Create a regular file
        test_file = raw_dir / "test.json"
        test_file.write_bytes(b"{}")
        
        old_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            hashes = collect_all_artifact_hashes([Path("data/raw")])
            assert len(hashes) == 1
            assert ".gitkeep" not in str(hashes)
        finally:
            os.chdir(old_cwd)

class TestUpdateStateRegistry:
    def test_create_new_state_file(self, tmp_path):
        """Test creation of a new state file."""
        state_file = tmp_path / "state.yaml"
        artifact_hashes = {"test.json": "abc123"}
        
        success = update_state_registry(state_file, artifact_hashes)
        
        assert success
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)
        
        assert state_data["artifact_hashes"] == artifact_hashes
        assert "updated_at" in state_data
        assert state_data["project_id"] == PROJECT_ID
    
    def test_update_existing_state_file(self, tmp_path):
        """Test updating an existing state file."""
        state_file = tmp_path / "state.yaml"
        
        # Create initial state
        initial_data = {
            "project_id": PROJECT_ID,
            "artifact_hashes": {"old.json": "oldhash"},
            "updated_at": "2023-01-01T00:00:00Z"
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_data, f)
        
        # Update with new hashes
        new_hashes = {"new.json": "newhash"}
        success = update_state_registry(state_file, new_hashes)
        
        assert success
        
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)
        
        # Verify update
        assert state_data["artifact_hashes"] == new_hashes
        assert "updated_at" in state_data
        # Verify timestamp changed
        assert state_data["updated_at"] != "2023-01-01T00:00:00Z"
    
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that the directory is created if it doesn't exist."""
        nested_state_file = tmp_path / "nested" / "deep" / "state.yaml"
        artifact_hashes = {"test.json": "abc123"}
        
        success = update_state_registry(nested_state_file, artifact_hashes)
        
        assert success
        assert nested_state_file.exists()

class TestIntegration:
    def test_full_workflow(self, tmp_path):
        """Test the complete workflow of collecting hashes and updating state."""
        # Setup temporary directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "processed").mkdir()
        (data_dir / "results").mkdir()
        
        # Create test files
        (data_dir / "raw" / "workflow1.json").write_bytes(b'{"id": 1}')
        (data_dir / "processed" / "log1.json").write_bytes(b'{"status": "ok"}')
        (data_dir / "results" / "threshold.json").write_bytes(b'{"threshold": 0.5}')
        
        state_file = tmp_path / "state.yaml"
        
        # Temporarily change working directory
        old_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Collect hashes
            artifact_hashes = collect_all_artifact_hashes(DATA_DIRS)
            assert len(artifact_hashes) == 3
            
            # Update state
            success = update_state_registry(state_file, artifact_hashes)
            assert success
            
            # Verify state file content
            with open(state_file, "r") as f:
                state_data = yaml.safe_load(f)
            
            assert len(state_data["artifact_hashes"]) == 3
            assert "raw/workflow1.json" in state_data["artifact_hashes"]
            assert "processed/log1.json" in state_data["artifact_hashes"]
            assert "results/threshold.json" in state_data["artifact_hashes"]
            assert "updated_at" in state_data
        finally:
            os.chdir(old_cwd)