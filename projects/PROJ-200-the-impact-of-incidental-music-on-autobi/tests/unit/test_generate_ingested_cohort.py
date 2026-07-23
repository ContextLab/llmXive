"""
Unit tests for generate_ingested_cohort module.

These tests verify the helper functions (checksum, state update) 
and ensure the module structure is correct.
"""
import os
import sys
import tempfile
import hashlib
import yaml
from pathlib import Path
import pytest
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_ingested_cohort import calculate_file_checksum, save_state_entry
from config import get_project_root

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_file_checksum(temp_dir):
    """Test that calculate_file_checksum returns a valid SHA-256 hex string."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    checksum = calculate_file_checksum(test_file)
    
    # Verify length (SHA-256 is 64 hex chars)
    assert len(checksum) == 64
    
    # Verify against known hash
    expected = hashlib.sha256(content).hexdigest()
    assert checksum == expected

def test_save_state_entry_creates_file(temp_dir):
    """Test that save_state_entry creates state.yaml if it doesn't exist."""
    state_file = temp_dir / "state.yaml"
    artifact_file = temp_dir / "data.parquet"
    artifact_file.write_bytes(b"fake data")
    
    save_state_entry(state_file, artifact_file, "abc123", "T018")
    
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "artifacts" in state
    assert "data.parquet" in state["artifacts"]
    assert state["artifacts"]["data.parquet"]["checksum"] == "abc123"
    assert state["artifacts"]["data.parquet"]["task_id"] == "T018"

def test_save_state_entry_updates_existing(temp_dir):
    """Test that save_state_entry updates existing state.yaml."""
    state_file = temp_dir / "state.yaml"
    existing_state = {
        "artifacts": {
            "old_file.parquet": {
                "path": "old_file.parquet",
                "checksum": "old_checksum",
                "task_id": "T001"
            }
        }
    }
    with open(state_file, 'w') as f:
        yaml.dump(existing_state, f)
    
    artifact_file = temp_dir / "new_file.parquet"
    artifact_file.write_bytes(b"new data")
    
    save_state_entry(state_file, artifact_file, "new_checksum", "T018")
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "old_file.parquet" in state["artifacts"]
    assert "new_file.parquet" in state["artifacts"]
    assert state["artifacts"]["new_file.parquet"]["checksum"] == "new_checksum"