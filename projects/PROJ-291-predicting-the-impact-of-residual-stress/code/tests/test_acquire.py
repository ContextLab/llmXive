"""
test_acquire.py
----------------
Integration test for the external‑dataset acquisition script (task T014).

The test runs the acquisition routine, then verifies two invariants:

1. ``data/external/acquisition_log.json`` exists and contains a top‑level
   ``openml`` and ``uci`` entry.
2. For every file recorded in the log with ``status == "success"``,
   the SHA‑256 checksum stored in ``data/raw/checksums.json`` matches the
   actual checksum of the file on disk.
"""

import json
from pathlib import Path

import pytest

from src.acquire_external import main as acquire_main

# Paths (relative to the project root)
CHECKSUMS_PATH = Path("data/raw/checksums.json")
LOG_PATH = Path("data/external/acquisition_log.json")

@pytest.fixture(scope="module")
def run_acquisition():
    """Execute the acquisition script once for the whole test module."""
    acquire_main()
    assert LOG_PATH.is_file(), "Acquisition log was not created"
    assert CHECKSUMS_PATH.is_file(), "Checksums file was not created"
    return {
        "log": json.loads(LOG_PATH.read_text(encoding="utf-8")),
        "checksums": json.loads(CHECKSUMS_PATH.read_text(encoding="utf-8")),
    }

def _file_checksum(path: Path) -> str:
    """Compute the SHA‑256 checksum of *path*."""
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_acquisition_log_structure(run_acquisition):
    """The log must contain the expected top‑level keys."""
    log = run_acquisition["log"]
    assert "openml" in log and "uci" in log, "Log missing required sections"
    # Both sections should have ``candidates`` and ``acquired`` lists.
    for section in ("openml", "uci"):
        assert isinstance(log[section]["candidates"], list)
        assert isinstance(log[section]["acquired"], list)

def test_checksums_match_acquired_files(run_acquisition):
    """
    For every successfully acquired file, the checksum stored in
    ``checksums.json`` must equal the actual file checksum.
    """
    log = run_acquisition["log"]
    checksums = run_acquisition["checksums"]

    for source in ("openml", "uci"):
        for entry in log[source]["acquired"]:
            if entry.get("status") != "success":
                continue  # Skip failed attempts – they raise earlier anyway.
            file_path = Path(entry["file"])
            assert file_path.is_file(), f"Acquired file missing: {file_path}"
            actual = _file_checksum(file_path)
            stored = checksums.get(str(file_path))
            assert stored is not None, f"No checksum recorded for {file_path}"
            assert actual == stored, f"Checksum mismatch for {file_path}"
