"""
Unit test for the ``download_data`` ingestion script (Task T002).

The test runs the script's ``main`` function, then checks that:
1. ``data/raw/checksums.json`` exists.
2. The manifest contains at least one file entry.
3. All listed files are present on disk.
"""
import json
from pathlib import Path

import pytest

# Import the script's main entry point.
from code.ingestion.download_data import main as download_main

@pytest.mark.integration
def test_download_and_checksum(tmp_path, monkeypatch):
    """
    Run the ingestion script and validate the checksum manifest.

    The test is marked as ``integration`` because it may download a real
    dataset from Hugging Face. It will be skipped on CI environments that
    lack internet access.
    """
    # Ensure a clean state: remove any pre‑existing raw directory.
    raw_root = Path("data") / "raw"
    if raw_root.is_dir():
        # Remove the directory tree to force a fresh download.
        import shutil
        shutil.rmtree(raw_root)

    # Execute the ingestion script. It should raise no exception.
    download_main()

    checksum_path = raw_root / "checksums.json"
    assert checksum_path.is_file(), "Checksum manifest was not created."

    with checksum_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Basic sanity checks on the manifest structure.
    assert isinstance(manifest, dict), "Manifest should be a dict."
    files = manifest.get("files")
    assert isinstance(files, list) and len(files) > 0, "Manifest must list at least one file."

    # Verify that every listed file actually exists.
    for entry in files:
        rel_path = Path(entry["path"])
        absolute_path = raw_root / rel_path
        assert absolute_path.is_file(), f"Listed file missing on disk: {rel_path}"
