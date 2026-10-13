"""
Integration test for the Devign download script.

The test invokes the `main` function defined in `code/download_devign.py`
and checks that:
  * The CSV file `data/raw/devign/devign.csv` exists after execution.
  * Its SHA‑256 checksum is recorded in `data/checksums.json`.
"""
import json
from pathlib import Path

import pytest

# Import the script as a module
from importlib import import_module

download_module = import_module("code.download_devign")

def test_download_and_checksum(tmp_path, monkeypatch):
    """
    Run the download script and verify output artifacts.
    The test relies on the real GitHub URL; if the URL becomes
    unavailable the test will fail, which is the intended behaviour.
    """
    # Ensure a clean state: remove any existing artefacts
    csv_path = Path("data/raw/devign/devign.csv")
    zip_path = Path("data/raw/devign/devign.zip")
    checksums_path = Path("data/checksums.json")

    for p in (csv_path, zip_path):
        if p.is_file():
            p.unlink()
    if checksums_path.is_file():
        # Remove only the entry for the CSV (keep others if present)
        with open(checksums_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.pop(str(csv_path), None)
        with open(checksums_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    # Run the main workflow
    download_module.main()

    # Assertions
    assert csv_path.is_file(), "CSV file was not created"
    assert zip_path.is_file(), "ZIP archive was not created"

    # Verify checksum entry exists and matches the computed value
    with open(checksums_path, "r", encoding="utf-8") as f:
        checksums = json.load(f)

    assert str(csv_path) in checksums, "Checksum entry missing in checksums.json"

    # Re‑compute checksum and compare
    from code.download_devign import compute_sha256

    recomputed = compute_sha256(csv_path)
    assert checksums[str(csv_path)] == recomputed, "Recorded checksum does not match file content"