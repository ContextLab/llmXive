"""
Integration test for the hash_artifacts utility.

This test ensures that executing `code/utils/hash_artifacts.py`
creates the canonical state file with the required structure.
"""
import json
import sys
import subprocess
from pathlib import Path

def test_hash_artifacts_creates_state_file():
    """
    Run the hash_artifacts script and verify that the state file
    `state/projects/PROJ-027-predict-antibiotic-resistance-evoluti.yaml`
    exists, is valid JSON/YAML, and contains the required keys.
    """
    script_path = Path("code/utils/hash_artifacts.py")
    assert script_path.is_file(), f"Script not found: {script_path}"

    # Execute the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"hash_artifacts exited with {result.returncode}\\n"
        f"stdout: {result.stdout}\\nstderr: {result.stderr}"
    )

    # Verify the state file exists
    state_path = Path("state/projects/PROJ-027-predict-antibiotic-resistance-evoluti.yaml")
    assert state_path.is_file(), f"State file not created at {state_path}"

    # Load the state file (JSON is also valid YAML)
    with open(state_path, "r", encoding="utf-8") as f:
        try:
            state_data = json.load(f)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"State file is not valid JSON/YAML: {exc}") from exc

    # Required top‑level keys
    for key in ("artifact_hashes", "updated_at"):
        assert key in state_data, f"Missing required key '{key}' in state file"

    # Ensure at least one artifact hash is recorded
    assert isinstance(state_data["artifact_hashes"], dict), (
        "artifact_hashes should be a mapping"
    )
    assert len(state_data["artifact_hashes"]) > 0, (
        "artifact_hashes mapping is empty"
    )