"""
Unit test for the checksum generation utility.

The test creates a temporary raw file, runs ``generate_checksums`` and then
verifies that the state YAML contains an entry for the newly created file.
"""
import os
import yaml
from pathlib import Path

from code.utils.checksums import generate_checksums

def test_generate_checksums(tmp_path):
    # ----------------------------------------------------------------------
    # Setup: ensure a clean ``data/raw`` directory and create a dummy file.
    # ----------------------------------------------------------------------
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    dummy_file = raw_dir / "dummy.txt"
    dummy_content = "checksum test content"
    dummy_file.write_text(dummy_content, encoding="utf-8")

    # Ensure the state file does not contain stale data from previous runs.
    state_file = Path(
        "state/projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml"
    )
    if state_file.parent.exists():
        # Remove any existing state file to guarantee a fresh start.
        for p in state_file.parent.iterdir():
            p.unlink()
    else:
        state_file.parent.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------------
    # Execute the checksum generation.
    # ----------------------------------------------------------------------
    generate_checksums()

    # ----------------------------------------------------------------------
    # Verify the YAML contains the expected mapping.
    # ----------------------------------------------------------------------
    assert state_file.is_file(), "State file was not created"

    with state_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "State file did not contain a YAML mapping"
    assert "artifact_hashes" in data, "Missing 'artifact_hashes' key in state file"

    artifact_hashes = data["artifact_hashes"]
    rel_path = dummy_file.as_posix()
    assert rel_path in artifact_hashes, f"Checksum for {rel_path} not recorded"

    # Clean up the dummy file (the raw directory may contain other files that are
    # part of the pipeline, so we only remove the one we created).
    dummy_file.unlink()
    # Optionally remove the raw directory if it is now empty.
    try:
        raw_dir.rmdir()
    except OSError:
        pass  # Directory not empty – leave it for other pipeline stages.