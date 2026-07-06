"""
Tests for the state_manager module.

These tests verify:
- File and directory hash calculation
- State file loading and saving
- Phase state recording
- Artifact integrity verification
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest
import sys
import hashlib

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_manager import (
    calculate_file_hash,
    calculate_directory_hash,
    load_state_file,
    save_state_file,
    record_phase_state,
    get_latest_phase_state,
    verify_artifact_integrity
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file in the temporary directory."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    return file_path


@pytest.fixture
def sample_dir(temp_dir):
    """Create a sample directory with files."""
    dir_path = temp_dir / "test_dir"
    dir_path.mkdir()
    (dir_path / "file1.txt").write_text("File 1 content")
    (dir_path / "file2.txt").write_text("File 2 content")
    return dir_path


@pytest.fixture
def state_file(temp_dir):
    """Create a sample state file."""
    state_path = temp_dir / "state.yaml"
    state_data = {
        "project": str(temp_dir),
        "phases": [
            {
                "phase_name": "Test Phase",
                "timestamp": "2024-01-01T00:00:00Z",
                "artifacts": [
                    {
                        "path": "test_file.txt",
                        "type": "file",
                        "hash": "abc123"
                    }
                ]
            }
        ],
        "last_updated": "2024-01-01T00:00:00Z"
    }
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f)
    return state_path


class TestCalculateFileHash:
    def test_calculate_file_hash(self, sample_file):
        """Test that file hash is calculated correctly."""
        content = sample_file.read_text()
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        actual_hash = calculate_file_hash(sample_file)
        assert actual_hash == expected_hash
    
    def test_calculate_file_hash_nonexistent(self, temp_dir):
        """Test that FileNotFoundError is raised for non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            calculate_file_hash(nonexistent)

class TestCalculateDirectoryHash:
    def test_calculate_directory_hash(self, sample_dir):
        """Test that directory hash is calculated correctly."""
        # The hash should be consistent for the same content
        hash1 = calculate_directory_hash(sample_dir)
        hash2 = calculate_directory_hash(sample_dir)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_calculate_directory_hash_content_change(self, sample_dir):
        """Test that hash changes when content changes."""
        hash1 = calculate_directory_hash(sample_dir)
        (sample_dir / "file1.txt").write_text("Modified content")
        hash2 = calculate_directory_hash(sample_dir)
        assert hash1 != hash2
    
    def test_calculate_directory_hash_nonexistent(self, temp_dir):
        """Test that FileNotFoundError is raised for non-existent directory."""
        nonexistent = temp_dir / "nonexistent_dir"
        with pytest.raises(FileNotFoundError):
            calculate_directory_hash(nonexistent)
    
    def test_calculate_directory_hash_not_dir(self, sample_file):
        """Test that NotADirectoryError is raised for a file path."""
        with pytest.raises(NotADirectoryError):
            calculate_directory_hash(sample_file)

class TestLoadSaveStateFile:
    def test_load_state_file_new(self, temp_dir):
        """Test loading a non-existent state file raises error."""
        state_path = temp_dir / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            load_state_file(state_path)
    
    def test_load_state_file_existing(self, state_file):
        """Test loading an existing state file."""
        state = load_state_file(state_file)
        assert "phases" in state
        assert len(state["phases"]) == 1
    
    def test_save_and_load_state_file(self, temp_dir):
        """Test saving and loading state."""
        state_path = temp_dir / "test_state.yaml"
        test_state = {
            "project": str(temp_dir),
            "phases": [],
            "last_updated": None
        }
        save_state_file(state_path, test_state)
        loaded = load_state_file(state_path)
        assert loaded == test_state

class TestRecordPhaseState:
    def test_record_phase_state(self, temp_dir):
        """Test recording a phase state."""
        # Create a test file
        test_file = temp_dir / "artifact.txt"
        test_file.write_text("Test content")
        
        state_path = temp_dir / "state.yaml"
        state = record_phase_state(
            phase_name="Test Phase",
            artifacts=[test_file],
            state_path=state_path,
            project_root=temp_dir
        )
        
        assert "phases" in state
        assert len(state["phases"]) == 1
        assert state["phases"][0]["phase_name"] == "Test Phase"
        assert len(state["phases"][0]["artifacts"]) == 1
        assert state["phases"][0]["artifacts"][0]["path"] == "artifact.txt"
        assert "hash" in state["phases"][0]["artifacts"][0]
    
    def test_record_phase_state_missing_artifact(self, temp_dir):
        """Test that FileNotFoundError is raised for missing artifact."""
        nonexistent = temp_dir / "nonexistent.txt"
        state_path = temp_dir / "state.yaml"
        
        with pytest.raises(FileNotFoundError):
            record_phase_state(
                phase_name="Test Phase",
                artifacts=[nonexistent],
                state_path=state_path,
                project_root=temp_dir
            )

class TestGetLatestPhaseState:
    def test_get_latest_phase_state(self, state_file):
        """Test getting the latest phase state."""
        latest = get_latest_phase_state(state_path=state_file)
        assert latest is not None
        assert latest["phase_name"] == "Test Phase"
    
    def test_get_latest_phase_state_empty(self, temp_dir):
        """Test getting latest state from empty state file."""
        state_path = temp_dir / "empty_state.yaml"
        save_state_file(state_path, {"phases": []})
        latest = get_latest_phase_state(state_path=state_path)
        assert latest is None
    
    def test_get_latest_phase_state_missing_file(self, temp_dir):
        """Test getting latest state from non-existent file."""
        state_path = temp_dir / "nonexistent.yaml"
        latest = get_latest_phase_state(state_path=state_path)
        assert latest is None

class TestVerifyArtifactIntegrity:
    def test_verify_artifact_integrity(self, temp_dir):
        """Test verifying artifact integrity."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")
        
        # Record state
        state_path = temp_dir / "state.yaml"
        record_phase_state(
            phase_name="Test",
            artifacts=[test_file],
            state_path=state_path,
            project_root=temp_dir
        )
        
        # Verify
        result = verify_artifact_integrity(
            artifacts=[test_file],
            state_path=state_path,
            project_root=temp_dir
        )
        
        assert result["valid"] is True
        assert len(result["details"]) == 1
        assert result["details"][0]["status"] == "valid"
    
    def test_verify_artifact_integrity_missing(self, temp_dir):
        """Test verification with missing artifact."""
        nonexistent = temp_dir / "nonexistent.txt"
        state_path = temp_dir / "state.yaml"
        
        result = verify_artifact_integrity(
            artifacts=[nonexistent],
            state_path=state_path,
            project_root=temp_dir
        )
        
        assert result["valid"] is False
        assert len(result["details"]) == 1
        assert result["details"][0]["status"] == "error"
    
    def test_verify_artifact_integrity_missing_key(self, temp_dir):
        """Test verification when artifact not in state."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")
        
        # Create state without this artifact
        state_path = temp_dir / "state.yaml"
        save_state_file(state_path, {"phases": []})
        
        result = verify_artifact_integrity(
            artifacts=[test_file],
            state_path=state_path,
            project_root=temp_dir
        )
        
        assert result["valid"] is False
        assert len(result["details"]) == 1
        assert result["details"][0]["status"] == "missing"
