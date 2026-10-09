"""
Unit test for the state versioning script.

The test creates a temporary file inside the project, runs the
``record_state_snapshot`` function, and verifies that the resulting
snapshot JSON contains a SHA‑256 entry for the temporary file.
"""

import json
import tempfile
from pathlib import Path

# Import the helper directly from the module under test.
from state_manager import compute_sha256, record_state_snapshot

def test_record_state_snapshot_creates_valid_json(tmp_path: Path):
    # Arrange: create a dummy artifact file.
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("state versioning test")

    # Act: record a snapshot for this single file.
    snapshot_path = tmp_path / "snapshot.json"
    record_state_snapshot([dummy_file], output_file=snapshot_path)

    # Assert: the snapshot file exists and contains the correct hash.
    assert snapshot_path.is_file(), "Snapshot JSON was not created"

    with snapshot_path.open() as f:
        snapshot_data = json.load(f)

    # The snapshot format is a mapping from relative file paths to hashes.
    # ``record_state_snapshot`` stores absolute paths; we normalise for the test.
    expected_hash = compute_sha256(dummy_file)
    # The JSON may store a dict under a top‑level key; inspect both possibilities.
    if isinstance(snapshot_data, dict) and "artifacts" in snapshot_data:
        artifact_dict = snapshot_data["artifacts"]
    else:
        artifact_dict = snapshot_data

    # Find the entry that matches our dummy file.
    found = any(
        entry.get("path") == str(dummy_file) and entry.get("sha256") == expected_hash
        for entry in artifact_dict.values()
        if isinstance(entry, dict)
    )
    assert found, "Snapshot does not contain the expected SHA‑256 entry for dummy.txt"