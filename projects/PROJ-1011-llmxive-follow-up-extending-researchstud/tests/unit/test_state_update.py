"""Verification for T006: state-management helper records artifact hashes."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.update_state import (  # noqa: E402
    MANIFEST_PATH,
    get_artifact_state,
    update_state_for_artifact,
    verify_artifact_integrity,
)


def test_state_update(tmp_path):
    dummy = tmp_path / "dummy_artifact.txt"
    dummy.write_text("hello artifact tracking\n")

    entry = update_state_for_artifact(
        dummy, "T006", "dummy artifact for verification"
    )

    # Manifest lives under the project-owned data/state/ path.
    assert MANIFEST_PATH.exists()
    assert MANIFEST_PATH.is_relative_to(PROJECT_ROOT / "data")

    manifest = json.loads(MANIFEST_PATH.read_text())
    # The recorded key is the absolute path (outside project tree in tmp).
    assert dummy.resolve().as_posix() in manifest["artifacts"] or any(
        v["metadata"]["checksum"] == entry["metadata"]["checksum"]
        for v in manifest["artifacts"].values()
    )

    # Hash is recorded and matches the file content.
    state = get_artifact_state(dummy)
    assert state is not None
    assert state["task_id"] == "T006"
    assert state["metadata"]["checksum"] == entry["metadata"]["checksum"]
    assert len(state["metadata"]["checksum"]) == 64
    assert verify_artifact_integrity(dummy)

    # Integrity fails after modification.
    dummy.write_text("tampered\n")
    assert not verify_artifact_integrity(dummy)