import os
import yaml
import hashlib
import pytest
from llmxive_toolkit import paths

def get_file_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def test_state_yaml_hashes():
    """
    Verifies that the project state YAML exists and contains SHA-256 hashes 
    that match the actual files on disk.
    """
    # Updated to match the re-scoped project-owned path
    state_path = paths.data("raw", "project_state.yaml")
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    checksums_path = paths.data("raw", "checksums.json")

    if not state_path.exists():
        pytest.fail(f"State file missing: {state_path}")

    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)

    # Check for required keys
    required_keys = ["tasks_json_sha256", "skills_json_sha256", "checksums_json_sha256", "generated_at"]
    for key in required_keys:
        assert key in state, f"Missing key {key} in state file"

    # Verify hashes match actual disk content
    assert state["tasks_json_sha256"] == get_file_sha256(tasks_path), "tasks.json hash mismatch"
    assert state["skills_json_sha256"] == get_file_sha256(skills_path), "skills.json hash mismatch"
    assert state["checksums_json_sha256"] == get_file_sha256(checksums_path), "checksums.json hash mismatch"

def test_state_yaml_timestamp():
    """Verifies that the generated_at field is a valid ISO timestamp."""
    state_path = paths.data("raw", "project_state.yaml")
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    
    timestamp = state.get("generated_at", "")
    assert timestamp.endswith("Z"), "Timestamp should be in UTC (end with Z)"
    assert len(timestamp) > 10, "Timestamp is too short to be valid ISO"