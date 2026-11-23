import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.state_manager import compute_file_hash, update_state_artifact, load_state, verify_artifact_integrity
from src.utils.config import get_project_root

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_csv(temp_state_dir):
    """Create a sample CSV file for testing."""
    csv_path = temp_state_dir / "test_data.csv"
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"]
    })
    df.to_csv(csv_path, index=False)
    return csv_path

def test_compute_file_hash(sample_csv):
    """Test that compute_file_hash returns a valid SHA-256 hash."""
    file_hash = compute_file_hash(sample_csv)
    
    # Verify it's a 64-character hex string (SHA-256)
    assert len(file_hash) == 64
    assert all(c in '0123456789abcdef' for c in file_hash)
    
    # Verify hash is deterministic
    hash_again = compute_file_hash(sample_csv)
    assert file_hash == hash_again

def test_compute_file_hash_missing_file(temp_state_dir):
    """Test that compute_file_hash raises FileNotFoundError for missing file."""
    missing_path = temp_state_dir / "nonexistent.csv"
    
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_path)

def test_update_state_with_hashes(temp_state_dir, sample_csv):
    """Test that update_state_artifact correctly updates the state file."""
    # Mock the state root to use our temp directory
    with patch('src.utils.state_manager.get_state_root', return_value=temp_state_dir):
        with patch('src.utils.state_manager.get_project_root', return_value=Path("/test/project")):
            artifact_name = "test_artifact.csv"
            update_state_artifact(artifact_name, sample_csv, "Test artifact")
            
            # Load state and verify
            state = load_state()
            assert "artifacts" in state
            assert artifact_name in state["artifacts"]
            
            artifact_info = state["artifacts"][artifact_name]
            assert artifact_info["path"] == str(sample_csv)
            assert "hash" in artifact_info
            assert "updated_at" in artifact_info
            assert artifact_info["description"] == "Test artifact"

def test_update_state_missing_file(temp_state_dir):
    """Test that update_state_artifact raises error for missing file."""
    missing_path = temp_state_dir / "nonexistent.csv"
    
    with patch('src.utils.state_manager.get_state_root', return_value=temp_state_dir):
        with patch('src.utils.state_manager.get_project_root', return_value=Path("/test/project")):
            with pytest.raises(FileNotFoundError):
                update_state_artifact("test.csv", missing_path)

def test_missing_file_handling(temp_state_dir, sample_csv):
    """Test hash verification with missing file."""
    # First, update state with a valid file
    with patch('src.utils.state_manager.get_state_root', return_value=temp_state_dir):
        with patch('src.utils.state_manager.get_project_root', return_value=Path("/test/project")):
            update_state_artifact("valid.csv", sample_csv)
            
            # Verify it passes
            assert verify_artifact_integrity("valid.csv") is True
            
            # Now delete the file
            sample_csv.unlink()
            
            # Verify it fails
            assert verify_artifact_integrity("valid.csv") is False

def test_state_file_creation(temp_state_dir):
    """Test that state file is created if it doesn't exist."""
    with patch('src.utils.state_manager.get_state_root', return_value=temp_state_dir):
        with patch('src.utils.state_manager.get_project_root', return_value=Path("/test/project")):
            state = load_state()
            
            # Should create initial state structure
            assert "artifacts" in state
            assert isinstance(state["artifacts"], dict)
            assert state.get("last_updated") is None
