"""Integration test for ``code/fetch_atomic_seeds.py``.

The test runs the script, checks that at least five seed files exist under
``data/raw/atomic_seeds/`` and verifies that each file’s SHA‑256 checksum matches
the entry recorded in ``data/checksums.txt``.
"""

import pathlib
import hashlib

import subprocess
import sys

import pytest


SEED_DIR = pathlib.Path("data/raw/atomic_seeds")
CHECKSUM_FILE = pathlib.Path("data/checksums.txt")


def compute_sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.mark.integration
def test_fetch_atomic_seeds():
    """Run the fetch script and validate outputs."""
    # Execute the script
    result = subprocess.run(
        [sys.executable, "code/fetch_atomic_seeds.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check that at least five files are present
    seed_files = list(SEED_DIR.glob("*"))
    assert len(seed_files) >= 5, f"Expected ≥5 seed files, found {len(seed_files)}"

    # Load the checksum manifest
    manifest = {}
    with CHECKSUM_FILE.open() as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                checksum, rel_path = parts
                manifest[rel_path] = checksum

    # Verify each downloaded file has a matching checksum entry
    for path in seed_files:
        rel = path.as_posix()
        assert rel in manifest, f"{rel} missing from checksum manifest"
        expected = manifest[rel]
        actual = compute_sha256(path)
        assert actual == expected, f"Checksum mismatch for {rel}"