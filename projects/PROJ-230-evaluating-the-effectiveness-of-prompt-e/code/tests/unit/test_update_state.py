"""
Unit tests for update_state.py
"""
import os
import yaml
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.update_state import (
    ensure_state_dirs,
    load_state,
    save_state,
    compute_sha256,
    update_artifact_hash,
    scan_and_update_artifacts,
    update_checksums_state,
    get_state_summary
)

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def project_id():
    return "PROJ-230-test"

def test_ensure_state_dirs(temp_state_dir):
    """Test that ensure_state_dirs creates the necessary directories."""
    ensure_state_dirs(temp_state_dir)
    
    assert (temp_state_dir / "projects").exists()
    assert (temp_state_dir / "checksums").exists()

def test_load_state_new_project(temp_state_dir, project_id):
    """Test loading state for a new project."""
    state = load_state(temp_state_dir, project_id)
    
    assert state["project_id"] == project_id
    assert "created_at" in state
    assert "updated_at" in state
    assert "artifacts" in state
    assert "checksums" in state
    assert "summary" in state

def test_load_state_existing_project(temp_state_dir, project_id):
    """Test loading state for an existing project."""
    # First save a state
    initial_state = {
        "project_id": project_id,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "artifacts": {"test.txt": {"hash": "abc123"}},
        "checksums": {},
        "summary": {}
    }
    save_state(temp_state_dir, project_id, initial_state)
    
    # Load it back
    state = load_state(temp_state_dir, project_id)
    
    assert state["project_id"] == project_id
    assert state["artifacts"]["test.txt"]["hash"] == "abc123"

def test_update_artifact_hash(temp_state_dir, project_id):
    """Test updating artifact hash."""
    # Create a test file
    test_file = temp_state_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    state = load_state(temp_state_dir, project_id)
    state = update_artifact_hash(state, "test.txt", test_file)
    
    assert "test.txt" in state["artifacts"]
    assert state["artifacts"]["test.txt"]["hash"] == compute_sha256(test_file)
    assert "size_bytes" in state["test.txt"]

def test_scan_and_update_artifacts(temp_state_dir, project_id):
    """Test scanning and updating artifacts."""
    # Create test files
    test_dir = temp_state_dir / "data" / "raw"
    test_dir.mkdir(parents=True)
    
    file1 = test_dir / "file1.txt"
    file1.write_text("Content 1")
    
    file2 = test_dir / "file2.txt"
    file2.write_text("Content 2")
    
    state = load_state(temp_state_dir, project_id)
    state = scan_and_update_artifacts(temp_state_dir, project_id, [test_dir])
    
    # Check that both files are tracked
    assert len(state["artifacts"]) == 2
    assert any("file1.txt" in k for k in state["artifacts"].keys())
    assert any("file2.txt" in k for k in state["artifacts"].keys())

def test_update_checksums_state(temp_state_dir, project_id):
    """Test updating checksums state."""
    # Create a checksum file
    checksum_file = temp_state_dir / "checksums.txt"
    checksum_content = "abc123  data/raw/file1.txt\ndef456  data/raw/file2.txt\n"
    checksum_file.write_text(checksum_content)
    
    state = load_state(temp_state_dir, project_id)
    state = update_checksums_state(temp_state_dir, project_id, checksum_file)
    
    assert len(state["checksums"]) == 2
    assert state["checksums"]["data/raw/file1.txt"] == "abc123"
    assert state["checksums"]["data/raw/file2.txt"] == "def456"

def test_get_state_summary(temp_state_dir, project_id):
    """Test generating state summary."""
    state = {
        "project_id": project_id,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "artifacts": {"a.txt": {}, "b.txt": {}},
        "checksums": {"c.txt": "hash1", "d.txt": "hash2"},
        "summary": {}
    }
    
    summary = get_state_summary(state)
    
    assert summary["total_artifacts"] == 2
    assert summary["total_checksums"] == 2
    assert len(summary["artifact_paths"]) == 2

def test_save_state_updates_timestamp(temp_state_dir, project_id):
    """Test that saving state updates the timestamp."""
    state = load_state(temp_state_dir, project_id)
    initial_updated = state["updated_at"]
    
    # Wait a tiny bit to ensure time difference
    import time
    time.sleep(0.01)
    
    save_state(temp_state_dir, project_id, state)
    
    state = load_state(temp_state_dir, project_id)
    assert state["updated_at"] > initial_updated
