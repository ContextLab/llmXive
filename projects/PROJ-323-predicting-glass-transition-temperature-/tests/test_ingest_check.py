"""
test_ingest_check.py

Integration test that ensures the ``code.ingest`` module can both
download the Tg dataset and subsequently verify its checksum.
"""

import os
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the module under test.
from code import ingest as ingest_mod

@pytest.mark.timeout(300)
def test_download_and_checksum(tmp_path, monkeypatch):
    """
    Run the download path (no ``--check``) and then verify that the
    checksum file and the dataset exist and are consistent.
    """
    # Ensure a clean state: remove any existing raw data or checksum file.
    raw_dir = paths.data("raw")
    checksum_path = paths.data("checksums.json")
    if raw_dir.is_dir():
        for p in raw_dir.iterdir():
            p.unlink()
    if checksum_path.is_file():
        checksum_path.unlink()

    # Run the download (this will also create checksums.json)
    ingest_mod._main()

    # After download, both files must exist.
    assert checksum_path.is_file(), "checksums.json was not created"
    assert (raw_dir / "tg_dataset.csv").is_file(), "tg_dataset.csv was not created"

    # Load the recorded checksum and compare with actual file checksum.
    with checksum_path.open() as f:
        recorded = json.load(f)
    assert "tg_dataset.csv" in recorded, "Checksum entry missing for tg_dataset.csv"

    # Compute actual checksum directly.
    def compute_sha256(p: Path) -> str:
        import hashlib

        sha = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    actual_checksum = compute_sha256(raw_dir / "tg_dataset.csv")
    assert (
        actual_checksum.lower() == recorded["tg_dataset.csv"].lower()
    ), "Recorded checksum does not match actual file checksum"

    # Finally, run the ``--check`` verification path – it should exit cleanly.
    # We capture stdout/stderr to ensure no exception is raised.
    ingest_mod._main()  # without ``--check`` just re‑downloads (idempotent)
    # Now invoke the check mode.
    ingest_mod._parse_args = lambda: type("Args", (), {"check": True})()
    ingest_mod._main()