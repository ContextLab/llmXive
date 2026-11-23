"""
Unit tests for save_processed_data.py logic.
These tests verify that the saving and hashing logic works correctly.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils import compute_file_hash, load_state, update_state

def test_compute_file_hash():
    """Test that compute_file_hash returns a valid SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n1,2\n3,4")
        temp_path = Path(f.name)

    try:
        hash_val = compute_file_hash(temp_path)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA-256 hex length
        # Verify it matches expected hash of the content
        expected_content = "col1,col2\n1,2\n3,4"
        expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()
        assert hash_val == expected_hash
    finally:
        os.unlink(temp_path)

def test_update_state():
    """Test that update_state correctly writes the state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        initial_state = {
            "version": 1,
            "artifacts": {}
        }
        
        # Write initial state manually to simulate existing file
        import yaml
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)

        # Update state
        new_state = load_state(state_file)
        new_state["artifacts"]["test_artifact"] = {
            "path": "data/test.csv",
            "hash": "abc123"
        }
        update_state(state_file, new_state)

        # Verify
        loaded = load_state(state_file)
        assert loaded["artifacts"]["test_artifact"]["hash"] == "abc123"
        assert loaded["artifacts"]["test_artifact"]["path"] == "data/test.csv"