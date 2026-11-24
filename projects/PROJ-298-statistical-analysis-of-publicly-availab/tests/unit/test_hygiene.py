"""
Unit tests for the hygiene utilities (SHA-256 hashing and state file updates).
The tests verify that:
1. A sample file can be hashed correctly.
2. The state YAML file is created (if missing) and contains the correct checksum
   entry after invoking `update_artifact_checksums`.
"""

import json
import hashlib
import os
import sys
import tempfile
from pathlib import Path

# Add the project’s `code` directory to the import path so we can import the module.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.append(str(CODE_DIR))

# Import the hygiene module
from utils import hygiene

def test_calculate_sha256_and_state_update(tmp_path: Path):
    """
    Create a temporary file, compute its SHA-256 hash using the hygiene utility,
    run `update_artifact_checksums`, and verify that the state file contains the
    expected entry.
    """
    # 1️⃣ Create a temporary file with known content
    sample_content = b"llmXive hygiene test data"
    sample_file = tmp_path / "sample.txt"
    sample_file.write_bytes(sample_content)

    # Expected hash (computed directly)
    expected_hash = hashlib.sha256(sample_content).hexdigest()

    # 2️⃣ Ensure the state file does NOT exist before the call
    state_path = PROJECT_ROOT / hygiene.DEFAULT_STATE_PATH
    if state_path.exists():
        state_path.unlink()

    # 3️⃣ Call the utility to update checksums
    # The function expects a list of string paths; we pass the absolute path.
    hygiene.update_artifact_checksums([str(sample_file)])

    # 4️⃣ Verify the state file was created
    assert state_path.is_file(), "State file was not created."

    # 5️⃣ Load the state file and locate the checksum entry
    with open(state_path, "r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f)

    # Determine the key used for the artifact (relative to cwd)
    try:
        rel_path = sample_file.resolve().relative_to(Path.cwd())
    except ValueError:
        rel_path = sample_file.resolve()
    artifact_key = str(rel_path)

    # The checksum should be stored under artifacts -> processed (default)
    stored_entry = (
        state_data.get("artifacts", {})
        .get("processed", {})
        .get(artifact_key, {})
    )
    assert stored_entry, f"Checksum entry for {artifact_key} missing in state."

    # 6️⃣ Verify the stored checksum matches the expected hash
    assert (
        stored_entry["checksum"] == expected_hash
    ), f"Checksum mismatch: expected {expected_hash}, got {stored_entry['checksum']}"

    # Cleanup: remove the temporary state file to avoid side‑effects for other tests
    state_path.unlink()