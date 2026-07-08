"""
Unit test for T005b: Verify versioning.py runs successfully on a dummy artifact
and updates state YAML correctly.
"""
import os
import yaml
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path to import versioning
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from versioning import (
    compute_sha256,
    load_state,
    save_state,
    update_version_state,
    DEFAULT_STATE_FILE
)

def test_versioning_on_dummy_artifact():
    """
    Test that versioning.py successfully computes a hash for a dummy file
    and updates the state YAML file correctly.
    """
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a dummy artifact file
        dummy_file = tmp_path / "dummy_artifact.txt"
        dummy_content = "This is a test artifact for versioning verification."
        dummy_file.write_text(dummy_content)
        
        # Define state file path
        state_file = tmp_path / "test_state.yaml"
        
        # Verify compute_sha256 works on the dummy file
        expected_hash = compute_sha256(dummy_file)
        assert len(expected_hash) == 64, "SHA-256 hash should be 64 characters"
        assert all(c in '0123456789abcdef' for c in expected_hash), "Hash should be hex"
        
        # Run update_version_state with the dummy file
        # We need to pass the file relative to the project root (tmp_path)
        targets = ["dummy_artifact.txt"]
        state = update_version_state(
            targets=targets,
            state_file=state_file,
            project_root=tmp_path
        )
        
        # Verify state file exists
        assert state_file.exists(), "State file should be created"
        
        # Load and verify state content
        loaded_state = load_state(state_file)
        
        assert "last_updated" in loaded_state, "State should have last_updated"
        assert "project" in loaded_state, "State should have project name"
        assert loaded_state["project"] == "PROJ-786-multi-property-trade-offs-in-alloy-desig", \
            "Project name should match"
        assert "artifacts" in loaded_state, "State should have artifacts"
        assert "dummy_artifact.txt" in loaded_state["artifacts"], \
            "Dummy artifact should be in artifacts"
        
        artifact_info = loaded_state["artifacts"]["dummy_artifact.txt"]
        assert artifact_info["type"] == "file", "Artifact type should be 'file'"
        assert artifact_info["hash"] == expected_hash, "Hash should match computed hash"
        assert artifact_info["path"] == "dummy_artifact.txt", "Path should be correct"
        
        print("✓ T005b verification passed: versioning.py successfully processed dummy artifact")
        print(f"  - Artifact: {dummy_file}")
        print(f"  - Hash: {expected_hash[:16]}...")
        print(f"  - State file: {state_file}")
        
        return True

if __name__ == "__main__":
    success = test_versioning_on_dummy_artifact()
    if success:
        print("\nT005b: PASSED")
        exit(0)
    else:
        print("\nT005b: FAILED")
        exit(1)
