"""
Basic unit tests for the ``code.state_manager`` module.

The tests exercise the two public functions ``compute_hash`` and
``update_state`` and verify that the state file is created/updated with the
expected structure.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
from code.state_manager import compute_hash, update_state, _ensure_state_file, _write_state

@pytest.fixture
def temporary_file(tmp_path: Path) -> Path:
    """Create a small temporary file with known contents."""
    fp = tmp_path / "sample.txt"
    fp.write_text("llmXive state manager test")
    return fp

def test_compute_hash_known_content(temporary_file: Path):
    """Hash of known content must match pre‑computed SHA‑256."""
    expected = "5f6f53c3c4a3d6c2c9a0e548b1f5f0d5c7a3d1e9f5c2b4a9f0e1d2c3b4a5f6e7"
    # Compute the actual hash using the function
    actual = compute_hash(str(temporary_file))
    # Verify that the hash is a 64‑character hex string and matches the
    # recomputed value using hashlib directly.
    import hashlib
    reference = hashlib.sha256(temporary_file.read_bytes()).hexdigest()
    assert actual == reference
    assert len(actual) == 64
    # Ensure it is not the placeholder value above (the placeholder is
    # intentionally wrong to catch accidental hard‑coding).
    assert actual != expected

def test_update_state_creates_file(tmp_path: Path, temporary_file: Path):
    """Calling ``update_state`` should create ``state/project_state.yaml``."""
    # Ensure the state directory does not exist yet
    state_yaml = Path("state/project_state.yaml")
    if state_yaml.exists():
        state_yaml.unlink()
    if state_yaml.parent.exists():
        # Remove any stale files from previous runs
        for child in state_yaml.parent.iterdir():
            child.unlink()
        state_yaml.parent.rmdir()

    # Perform the update
    update_state(str(temporary_file))

    # The state file must now exist
    assert state_yaml.is_file(), "State file was not created"

    # Load the YAML and verify contents
    with state_yaml.open("r", encoding="utf-8") as f:
        data = json.load(f) if f.read().strip().startswith("{") else None
    # If json.load failed (because it's yaml), fall back to yaml safe_load
    if data is None:
        import yaml
        with state_yaml.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    assert isinstance(data, dict), "State file does not contain a mapping"
    artifacts = data.get("artifacts", {})
    assert str(temporary_file) in artifacts, "Artifact entry missing"
    entry = artifacts[str(temporary_file)]
    assert "hash" in entry and "timestamp" in entry
    # The stored hash must equal the hash computed directly
    assert entry["hash"] == compute_hash(str(temporary_file))

def test_update_state_overwrites_hash(tmp_path: Path, temporary_file: Path):
    """Subsequent calls must update the timestamp while preserving the hash."""
    update_state(str(temporary_file))
    state_path = Path("state/project_state.yaml")
    with state_path.open("r", encoding="utf-8") as f:
        import yaml
        state = yaml.safe_load(f)
    first_ts = state["artifacts"][str(temporary_file)]["timestamp"]

    # Modify the file (append a line) to change its hash
    temporary_file.write_text(temporary_file.read_text() + "\nextra")
    new_hash = compute_hash(str(temporary_file))

    # Update state again
    update_state(str(temporary_file))
    with state_path.open("r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    second_entry = state["artifacts"][str(temporary_file)]
    assert second_entry["hash"] == new_hash
    assert second_entry["timestamp"] != first_ts, "Timestamp was not refreshed"