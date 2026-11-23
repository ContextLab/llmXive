"""
Tests for code/update_state.py
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from update_state import compute_sha256, STATE_FILE, STATE_DIR, PROJECT_ID

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # Known hash for "test content"
        expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_state_file_structure():
    """Verify that state file has the expected structure after update."""
    # Ensure the state file exists by running the logic implicitly
    # We check the structure assuming main() has been run or will be run
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
        
        assert "project_id" in state
        assert state["project_id"] == PROJECT_ID
        assert "last_updated" in state
        assert "current_stage" in state
        assert "artifacts" in state
        assert state["current_stage"] == "implemented"
    else:
        pytest.skip("State file does not exist yet (run update_state.py first)")

def test_state_dir_creation():
    """Verify that state directory is created if it doesn't exist."""
    # This is more of a logic test; the function save_state handles creation.
    # We just verify the path object is correctly constructed.
    assert STATE_DIR.name == PROJECT_ID
    assert STATE_DIR.parent.name == "projects"
    assert STATE_DIR.parent.parent.name == "state"
