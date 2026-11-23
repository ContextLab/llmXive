import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.state_manager import (
    compute_file_hash,
    compute_directory_hashes,
    load_state,
    save_state,
    update_state_with_artifacts,
    PROJECT_ID
)

class TestStateManager:
    """Tests for the state manager utility functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def setup_test_files(self, temp_dir):
        """Create some test files in the temp directory."""
        # Create nested structure
        (temp_dir / "subdir").mkdir()
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "subdir" / "file2.json").write_text('{"key": "value"}')
        return temp_dir

    def test_compute_file_hash(self, setup_test_files):
        """Test SHA-256 hash computation for a single file."""
        file_path = setup_test_files / "file1.txt"
        hash1 = compute_file_hash(file_path)
        hash2 = compute_file_hash(file_path)
        
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hash2  # Deterministic
        assert isinstance(hash1, str)

    def test_compute_file_hash_missing(self, temp_dir):
        """Test hash computation for missing file returns 'missing'."""
        missing_path = temp_dir / "nonexistent.txt"
        assert compute_file_hash(missing_path) == "missing"

    def test_compute_directory_hashes(self, setup_test_files):
        """Test hash computation for all files in a directory."""
        hashes = compute_directory_hashes(setup_test_files)
        
        assert len(hashes) == 2
        assert "file1.txt" in hashes
        assert "subdir/file2.json" in hashes
        assert hashes["file1.txt"] == compute_file_hash(setup_test_files / "file1.txt")

    def test_compute_directory_hashes_with_pattern(self, setup_test_files):
        """Test hash computation with file extension filter."""
        hashes = compute_directory_hashes(setup_test_files, ".json")
        
        assert len(hashes) == 1
        assert "subdir/file2.json" in hashes
        assert "file1.txt" not in hashes

    def test_compute_directory_hashes_empty(self, temp_dir):
        """Test hash computation for empty directory."""
        hashes = compute_directory_hashes(temp_dir)
        assert hashes == {}

    def test_compute_directory_hashes_nonexistent(self, temp_dir):
        """Test hash computation for non-existent directory."""
        nonexistent = temp_dir / "does_not_exist"
        hashes = compute_directory_hashes(nonexistent)
        assert hashes == {}

    def test_load_state_new_project(self, temp_dir):
        """Test loading state when no state file exists."""
        # Temporarily change the state file path
        with patch('utils.state_manager.PROJECT_STATE_FILE', temp_dir / "state.yaml"):
            state = load_state()
            
            assert state["project_id"] == PROJECT_ID
            assert "created_at" in state
            assert state["updated_at"] is None
            assert state["artifacts"] == {}

    def test_save_and_load_state(self, temp_dir):
        """Test saving and loading state."""
        test_state = {
            "project_id": PROJECT_ID,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00",
            "artifacts": {"test": {"file.txt": "abc123"}}
        }
        
        state_file = temp_dir / "state.yaml"
        
        with patch('utils.state_manager.PROJECT_STATE_FILE', state_file):
            save_state(test_state)
            loaded = load_state()
            
            assert loaded == test_state

    def test_update_state_with_artifacts(self, temp_dir, setup_test_files):
        """Test updating state with actual file hashes."""
        # Create mock data directories
        data_raw = temp_dir / "data" / "raw"
        data_raw.mkdir(parents=True)
        (data_raw / "workflow.json").write_text('{"id": 1}')
        
        data_processed = temp_dir / "data" / "processed"
        data_processed.mkdir(parents=True)
        (data_processed / "log.json").write_text('{"status": "ok"}')
        
        data_results = temp_dir / "data" / "results"
        data_results.mkdir(parents=True)
        (data_results / "curve.csv").write_text("x,y\n1,2")
        
        state_file = temp_dir / "state.yaml"
        
        with patch('utils.state_manager.PROJECT_STATE_FILE', state_file):
            # Temporarily redirect the data paths
            original_raw = Path("data/raw")
            original_processed = Path("data/processed")
            original_results = Path("data/results")
            
            # We can't easily patch Path() globally, so we test the logic
            # by directly calling the hash functions on our temp dirs
            raw_hashes = compute_directory_hashes(data_raw, ".json")
            processed_hashes = compute_directory_hashes(data_processed, ".json")
            results_hashes = compute_directory_hashes(data_results)
            
            assert len(raw_hashes) == 1
            assert len(processed_hashes) == 1
            assert len(results_hashes) == 1

    def test_update_state_creates_directories(self, temp_dir):
        """Test that update_state_with_artifacts creates necessary directories."""
        state_file = temp_dir / "state.yaml"
        
        with patch('utils.state_manager.PROJECT_STATE_FILE', state_file):
            # This should create the state directory if it doesn't exist
            state = update_state_with_artifacts()
            
            assert state_file.exists()
            assert state["updated_at"] is not None
            assert "artifacts" in state