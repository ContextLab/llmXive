"""
Integration test for the checksum manifest.

The test generates (or regenerates) ``data/checksums.json`` using the
``code.checksums.compute_checksums`` function and then verifies that every
entry in the manifest matches the actual SHA‑256 hash of the corresponding
file on disk.
"""

import json
import hashlib
from pathlib import Path

import pytest

# Import the function that creates the manifest
from code.checksums import compute_checksums

@pytest.fixture(scope="module")
def manifest_path(tmp_path_factory):
    """
    Ensure a fresh manifest is generated for the test module.
    """
    # The function writes to the project's data directory, which is
    # shared across tests. We invoke it once per test session.
    manifest = compute_checksums()
    return manifest

def test_manifest_contains_correct_hashes(manifest_path):
    """
    For each entry in the manifest, recompute the SHA‑256 hash of the
    referenced file and compare it to the stored value.
    """
    # Load the manifest
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Verify each file
    for rel_path, expected_hash in manifest.items():
        file_path = Path(rel_path)
        # Resolve relative to the current working directory (project root)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        assert file_path.is_file(), f"Manifest entry points to missing file: {rel_path}"

        # Compute SHA‑256
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()

        assert (
            actual_hash == expected_hash
        ), f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"