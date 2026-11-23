"""
Test for ``code/ingestion/checksums.py``.

The test runs the ``main`` function, then verifies that:
  1. ``data/checksums.txt`` exists.
  2. It contains a line for ``data/raw/dataset.csv``.
  3. The recorded hash matches the actual SHA‑256 hash of the file.
"""

import hashlib
from pathlib import Path

import pytest

# Import the script under test
from ingestion.checksums import main as compute_checksums

@pytest.fixture
def raw_dataset_path():
    """Path to the synthetic (or real) dataset used for the test."""
    return Path.cwd() / "data" / "raw" / "dataset.csv"

def _hash_file(file_path: Path) -> str:
    """Utility to compute SHA‑256 of a file (same logic as the script)."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_checksums_file_is_created_and_correct(raw_dataset_path: Path):
    # Ensure the raw dataset exists; if not, the test cannot proceed.
    assert raw_dataset_path.is_file(), f"Dataset file missing: {raw_dataset_path}"

    # Run the checksum generation script
    compute_checksums()

    checksum_file = Path.cwd() / "data" / "checksums.txt"
    assert checksum_file.is_file(), "checksums.txt was not created"

    # Read the manifest
    lines = checksum_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "checksums.txt is empty"

    # Build a lookup dict {relative_path: hash}
    manifest = {}
    for line in lines:
        parts = line.split(maxsplit=1)
        assert len(parts) == 2, f"Malformed line in checksums.txt: {line!r}"
        file_hash, rel_path = parts
        manifest[rel_path] = file_hash

    # Relative path we expect (project root based)
    expected_rel = str(raw_dataset_path.relative_to(Path.cwd()))
    assert expected_rel in manifest, f"{expected_rel} not found in checksums.txt"

    # Verify the stored hash matches the actual file hash
    actual_hash = _hash_file(raw_dataset_path)
    assert manifest[expected_rel] == actual_hash, (
        f"Hash mismatch for {expected_rel}: "
        f"expected {actual_hash}, got {manifest[expected_rel]}"
    )