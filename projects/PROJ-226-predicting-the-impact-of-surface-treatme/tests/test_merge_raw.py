"""
test_merge_raw.py

Integration test for the ``merge_raw`` script. The test invokes the
``main`` function, then verifies that:

* ``data/raw/adhesion_raw.csv`` exists and is non‑empty.
* The SHA‑256 checksum recorded in ``data/raw/checksums.txt`` matches the
  actual checksum of the merged file.
"""

import hashlib
from pathlib import Path

import pytest

from merge_raw import main as merge_main
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def run_merge():
    """Execute the merge script once for the module."""
    merge_main()
    yield
    # No teardown needed – the generated files are part of the pipeline artefacts.

def _compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def test_merged_file_exists_and_nonempty(run_merge):
    merged_path = paths.data("raw", "adhesion_raw.csv")
    assert merged_path.is_file(), "Merged CSV was not created."
    assert merged_path.stat().st_size > 0, "Merged CSV is empty."

def test_checksum_matches_manifest(run_merge):
    merged_path = paths.data("raw", "adhesion_raw.csv")
    checksum_path = paths.data("raw", "checksums.txt")
    assert checksum_path.is_file(), "checksums.txt does not exist."

    # Read the manifest and locate the line for adhesion_raw.csv
    with checksum_path.open("r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    matching = [ln for ln in lines if ln.endswith("adhesion_raw.csv")]
    assert matching, "No checksum entry for adhesion_raw.csv found in checksums.txt."

    recorded_checksum = matching[0].split()[0]
    actual_checksum = _compute_sha256(merged_path)
    assert recorded_checksum == actual_checksum, (
        f"Checksum mismatch: recorded {recorded_checksum}, actual {actual_checksum}"
    )