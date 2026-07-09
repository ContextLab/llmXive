"""
Tests for the checksum verification utility (T009).
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
import sys

# Add parent to path for imports if running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.checksum import (
    ensure_state_file,
    calculate_file_hash,
    update_artifact_hash,
    verify_artifacts,
    update_all_artifacts_in_directory,
    get_state,
    clear_artifact_hashes
)
from config import get_project_root

PROJECT_ROOT = get_project_root()
TEST_STATE_FILE = os.path.join(PROJECT_ROOT, "state", "projects", "PROJ-196-the-role-of-temporal-discounting-in-proc.yaml")

@pytest.fixture(autouse=True)
def setup_state_file():
    """Ensure state file exists before tests, and reset after."""
    # Create a temporary copy of the state file logic or ensure it exists
    ensure_state_file()
    yield
    # Cleanup: clear hashes to avoid polluting real state if tests run on real project
    clear_artifact_hashes()

def test_ensure_state_file_creates():
    """Test that ensure_state_file creates the directory and file if missing."""
    # Temporarily delete the file to test creation
    if os.path.exists(TEST_STATE_FILE):
        os.remove(TEST_STATE_FILE)
    
    ensure_state_file()
    
    assert os.path.exists(TEST_STATE_FILE)
    
    with open(TEST_STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    assert state["project_id"] == "PROJ-196-the-role-of-temporal-discounting-in-proc"
    assert "artifact_hashes" in state

def test_calculate_file_hash():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        hash_val = calculate_file_hash(temp_path)
        # Known SHA-256 for "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert hash_val == expected
    finally:
        os.unlink(temp_path)

def test_update_artifact_hash():
    """Test updating a hash for a real file."""
    # Create a temp file in data/processed to simulate an artifact
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "processed"), exist_ok=True)
    temp_artifact = os.path.join(PROJECT_ROOT, "data", "processed", "test_artifact.txt")
    
    with open(temp_artifact, "w") as f:
        f.write("Test content for checksum")
    
    try:
        # Update hash
        update_artifact_hash(temp_artifact, "Test Artifact")
        
        # Verify state file
        state = get_state()
        rel_path = os.path.relpath(temp_artifact, PROJECT_ROOT)
        
        assert rel_path in state["artifact_hashes"]
        assert state["artifact_hashes"][rel_path]["description"] == "Test Artifact"
        assert "hash" in state["artifact_hashes"][rel_path]
        
        # Verify integrity
        results = verify_artifacts()
        assert results[rel_path] is True
    finally:
        if os.path.exists(temp_artifact):
            os.unlink(temp_artifact)

def test_verify_artifacts_missing_file():
    """Test verification when a tracked file is missing."""
    # Manually inject a fake path into state
    with open(TEST_STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    state["artifact_hashes"]["nonexistent_file.csv"] = {"hash": "abc123", "description": "Missing"}
    
    with open(TEST_STATE_FILE, "w") as f:
        yaml.dump(state, f)
    
    results = verify_artifacts()
    assert results["nonexistent_file.csv"] is False

def test_update_all_artifacts_in_directory():
    """Test scanning a directory for artifacts."""
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "processed"), exist_ok=True)
    test_file = os.path.join(PROJECT_ROOT, "data", "processed", "scan_test.csv")
    
    with open(test_file, "w") as f:
        f.write("col1,col2\n1,2")
    
    try:
        count = update_all_artifacts_in_directory("data/processed", "*.csv", "Scan: ")
        assert count == 1
        
        state = get_state()
        rel_path = os.path.relpath(test_file, PROJECT_ROOT)
        assert rel_path in state["artifact_hashes"]
        assert state["artifact_hashes"][rel_path]["description"].startswith("Scan: ")
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
