"""
Unit test for the state‑management helper (code/utils/update_state.py).

The test creates a temporary file, registers it with the state helper,
and verifies that the manifest contains a matching entry with the correct
checksum.
"""

import hashlib
from pathlib import Path

import yaml

from code.utils.update_state import (
    update_state_for_artifact,
    get_artifact_state,
    ensure_state_dir,
    STATE_DIR,
)
from code.utils.data_manifest import calculate_file_checksum


def test_state_update(tmp_path):
    """
    Verify that calling ``update_state_for_artifact`` records the file
    checksum in ``state/manifest.yaml``.
    """
    # Ensure a clean state directory
    if STATE_DIR.exists():
        # Remove any existing manifest to avoid interference
        manifest_path = STATE_DIR / "manifest.yaml"
        if manifest_path.exists():
            manifest_path.unlink()
    else:
        ensure_state_dir()

    # Create a dummy artifact file
    dummy_file = tmp_path / "dummy.txt"
    dummy_content = b"Hello, state management helper!"
    dummy_file.write_bytes(dummy_content)

    # Compute the expected checksum using the same utility function
    expected_checksum = calculate_file_checksum(dummy_file)

    # Register the artifact
    entry = update_state_for_artifact(
        file_path=str(dummy_file),
        task_id="T006",
        description="Test dummy artifact",
        dependencies=[],
    )

    # Load the manifest directly to inspect it
    manifest_path = STATE_DIR / "manifest.yaml"
    assert manifest_path.is_file(), "Manifest file was not created"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = yaml.safe_load(f)

    # The key in the manifest should be the relative path from the project root
    rel_path = str(dummy_file.relative_to(Path.cwd()))
    assert rel_path in manifest_data["artifacts"], "Artifact entry missing in manifest"

    artifact_entry = manifest_data["artifacts"][rel_path]

    # Verify the stored checksum matches the expected one
    assert (
        artifact_entry["metadata"]["checksum"] == expected_checksum
    ), "Checksum recorded in manifest does not match actual file checksum"

    # Verify that ``get_artifact_state`` returns the same entry
    state_entry = get_artifact_state(str(dummy_file))
    assert state_entry is not None, "get_artifact_state returned None"
    assert (
        state_entry["metadata"]["checksum"] == expected_checksum
    ), "get_artifact_state returned mismatched checksum"